"""Core workflow engine using LangGraph."""
from typing import Dict, Any, List
from datetime import datetime
import uuid
import structlog
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import WorkflowState, TaskStatus, Task, create_initial_state
from agents.planner import PlanningAgent
from agents.executor_agent import ExecutorAgent
from config import settings

logger = structlog.get_logger()


class WorkflowEngine:
    """Main workflow engine using LangGraph for stateful execution."""
    
    def __init__(self):
        self.planner = PlanningAgent()
        self.executor_agent = ExecutorAgent()
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()
        self.logger = logger.bind(component="WorkflowEngine")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow graph."""
        graph = StateGraph(WorkflowState)
        
        # Add nodes
        graph.add_node("plan", self._plan_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("decide", self._decide_node)
        graph.add_node("handle_failure", self._handle_failure_node)
        graph.add_node("complete", self._complete_node)
        
        # Define edges
        graph.set_entry_point("plan")
        graph.add_edge("plan", "decide")
        graph.add_conditional_edges(
            "decide",
            self._should_continue,
            {
                "execute": "execute",
                "complete": "complete",
                "handle_failure": "handle_failure"
            }
        )
        graph.add_edge("execute", "decide")
        graph.add_edge("handle_failure", "decide")
        graph.add_edge("complete", END)
        
        return graph.compile(checkpointer=self.checkpointer)
    
    async def _plan_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Planning node: break down goal into tasks."""
        self.logger.info("Planning workflow", workflow_id=state["context"]["workflow_id"])
        
        goal = state["context"]["goal"]
        context = state.get("memory", {})
        
        try:
            tasks = await self.planner.plan_workflow(goal, context)
            
            # Convert to task format
            task_dict = {}
            for task_data in tasks:
                task: Task = {
                    "task_id": task_data["task_id"],
                    "name": task_data["name"],
                    "description": task_data["description"],
                    "action_type": task_data["action_type"],
                    "action_config": task_data["action_config"],
                    "status": TaskStatus.PENDING,
                    "dependencies": task_data.get("dependencies", []),
                    "retry_count": 0,
                    "error": None,
                    "result": None,
                    "started_at": None,
                    "completed_at": None,
                }
                task_dict[task["task_id"]] = task
            
            return {
                "tasks": task_dict,
                "next_tasks": [t["task_id"] for t in tasks if not t.get("dependencies")],
            }
            
        except Exception as e:
            self.logger.error("Planning failed", error=str(e))
            return {
                "errors": state["errors"] + [{
                    "step": "plan",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }],
                "context": {
                    **state["context"],
                    "status": "failed"
                }
            }
    
    async def _execute_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Execution node: execute the current task."""
        # Get next task to execute
        next_tasks = state.get("next_tasks", [])
        if not next_tasks:
            return {}
        
        current_task_id = next_tasks[0]
        task = state["tasks"][current_task_id]
        self.logger.info("Executing task", task_id=current_task_id, task_name=task["name"])
        
        # Update task status
        task["status"] = TaskStatus.IN_PROGRESS
        task["started_at"] = datetime.now()
        
        # Execute task
        result = await self.executor_agent.execute_task(task, state)
        
        task["completed_at"] = datetime.now()
        
        if result["status"] == "success":
            task["status"] = TaskStatus.COMPLETED
            task["result"] = result["data"]
            task["error"] = None
            
            # Update memory with result
            memory = state.get("memory", {})
            memory[f"task_{current_task_id}_result"] = result["data"]
            
            # Remove from next_tasks
            remaining_tasks = [tid for tid in state.get("next_tasks", []) if tid != current_task_id]
            
            return {
                "tasks": {**state["tasks"], current_task_id: task},
                "completed_tasks": state["completed_tasks"] + [current_task_id],
                "memory": memory,
                "execution_history": state["execution_history"] + [{
                    "task_id": current_task_id,
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "result": result["data"]
                }],
                "next_tasks": remaining_tasks,
                "current_task": None,
            }
        else:
            task["status"] = TaskStatus.FAILED
            task["error"] = result["error"]
            
            # Remove from next_tasks
            remaining_tasks = [tid for tid in state.get("next_tasks", []) if tid != current_task_id]
            
            return {
                "tasks": {**state["tasks"], current_task_id: task},
                "failed_tasks": state["failed_tasks"] + [current_task_id],
                "execution_history": state["execution_history"] + [{
                    "task_id": current_task_id,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat(),
                    "error": result["error"]
                }],
                "next_tasks": remaining_tasks,
                "current_task": None,
            }
    
    async def _decide_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Decision node: decide which tasks to execute next."""
        # Get all task IDs
        all_task_ids = list(state["tasks"].keys())
        completed = set(state["completed_tasks"])
        failed = set(state["failed_tasks"])
        
        # Find available tasks (not completed, not failed, dependencies met)
        available = []
        for task_id in all_task_ids:
            if task_id in completed or task_id in failed:
                continue
            
            task = state["tasks"][task_id]
            dependencies = task.get("dependencies", [])
            
            if all(dep in completed for dep in dependencies):
                available.append(task_id)
        
        if not available:
            # All tasks done or failed
            return {
                "next_tasks": [],
            }
        
        # Decide which tasks to execute next (can be parallel)
        next_tasks = await self.planner.decide_next_tasks(state, available)
        
        return {
            "next_tasks": next_tasks,
        }
    
    def _should_continue(self, state: WorkflowState) -> str:
        """Determine next step after decision."""
        next_tasks = state.get("next_tasks", [])
        
        if not next_tasks:
            # Check if we have failed tasks that need handling
            failed_tasks = [tid for tid in state.get("failed_tasks", []) 
                          if state["tasks"][tid]["retry_count"] < settings.max_retries]
            if failed_tasks:
                return "handle_failure"
            return "complete"
        
        # Set current task to first available
        return "execute"
    
    async def _handle_failure_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Handle task failures with retry logic."""
        failed_tasks = state.get("failed_tasks", [])
        if not failed_tasks:
            return {}
        
        # Get first failed task that can be retried
        task_to_retry = None
        for task_id in failed_tasks:
            task = state["tasks"][task_id]
            if task["retry_count"] < settings.max_retries:
                task_to_retry = task_id
                break
        
        if not task_to_retry:
            # All failed tasks exceeded retries
            return {
                "context": {
                    **state["context"],
                    "status": "failed",
                    "completed_at": datetime.now()
                }
            }
        
        task = state["tasks"][task_to_retry]
        
        # Get failure handling decision
        decision = await self.executor_agent.handle_failure(
            task,
            task["error"] or "Unknown error",
            state,
            task["retry_count"]
        )
        
        if decision["action"] == "retry":
            task["retry_count"] += 1
            task["status"] = TaskStatus.RETRYING
            task["error"] = None
            
            # Remove from failed tasks
            failed_tasks = [tid for tid in state["failed_tasks"] if tid != task_to_retry]
            
            return {
                "tasks": {**state["tasks"], task_to_retry: task},
                "failed_tasks": failed_tasks,
                "next_tasks": [task_to_retry],
                "current_task": task_to_retry,
            }
        elif decision["action"] == "skip":
            task["status"] = TaskStatus.SKIPPED
            failed_tasks = [tid for tid in state["failed_tasks"] if tid != task_to_retry]
            
            return {
                "tasks": {**state["tasks"], task_to_retry: task},
                "failed_tasks": failed_tasks,
            }
        else:  # fail_workflow
            return {
                "context": {
                    **state["context"],
                    "status": "failed",
                    "completed_at": datetime.now()
                }
            }
    
    
    async def _complete_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Completion node: finalize workflow."""
        completed_count = len(state["completed_tasks"])
        total_count = len(state["tasks"])
        failed_count = len(state["failed_tasks"])
        
        status = "completed"
        if failed_count > 0:
            status = "completed_with_errors"
        if state["context"]["status"] == "failed":
            status = "failed"
        
        self.logger.info(
            "Workflow completed",
            workflow_id=state["context"]["workflow_id"],
            status=status,
            completed=completed_count,
            total=total_count,
            failed=failed_count
        )
        
        return {
            "context": {
                **state["context"],
                "status": status,
                "completed_at": datetime.now()
            }
        }
    
    async def run(
        self,
        goal: str,
        workflow_id: str = None,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run a workflow from a goal.
        
        Args:
            goal: High-level goal description
            workflow_id: Optional workflow ID (generated if not provided)
            config: Optional workflow configuration
            
        Returns:
            Final workflow state
        """
        if workflow_id is None:
            workflow_id = str(uuid.uuid4())
        
        initial_state = create_initial_state(workflow_id, goal)
        if config:
            initial_state["context"]["metadata"].update(config)
        
        self.logger.info("Starting workflow", workflow_id=workflow_id, goal=goal)
        
        config_dict = {
            "configurable": {
                "thread_id": workflow_id
            }
        }
        
        # Stream execution and collect final state
        final_state = initial_state
        async for node_name, node_state in self.graph.astream(initial_state, config_dict):
            # Merge state updates
            for key, value in node_state.items():
                if isinstance(value, dict) and key in final_state:
                    final_state[key].update(value)
                else:
                    final_state[key] = value
            
            # Log progress
            if "next_tasks" in node_state:
                next_tasks = node_state.get("next_tasks", [])
                self.logger.debug("Workflow progress", node=node_name, next_tasks=next_tasks)
        
        return final_state

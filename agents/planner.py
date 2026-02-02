"""Planning agent that breaks down goals into executable tasks."""
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import json
import structlog

from config import settings

logger = structlog.get_logger()


class PlanningAgent:
    """Agent responsible for planning and task decomposition."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,  # Lower temperature for more deterministic planning
            api_key=settings.openai_api_key
        )
        self.logger = logger.bind(component="PlanningAgent")
    
    async def plan_workflow(self, goal: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Break down a high-level goal into executable tasks.
        
        Args:
            goal: High-level goal description
            context: Additional context for planning
            
        Returns:
            List of task dictionaries with action details
        """
        self.logger.info("Planning workflow", goal=goal, context=context)
        
        system_prompt = """You are an expert workflow planning agent. Your job is to break down high-level goals into concrete, executable tasks.

Each task should be:
1. Specific and actionable
2. Have clear dependencies (if any)
3. Include the action type (api_call, db_query, file_operation, transform_data, wait)
4. Include necessary configuration for execution

Available action types:
- api_call: HTTP API requests (needs: method, url, headers, body)
- db_query: Database operations (needs: query, params)
- file_operation: File read/write/delete/list (needs: operation, path, content if write)
- transform_data: Data transformation (needs: type, input, mapping)
- wait: Delay execution (needs: duration in seconds)

Return a JSON array of tasks. Each task should have:
- task_id: unique identifier
- name: descriptive name
- description: what this task does
- action_type: one of the action types above
- action_config: configuration object for the action
- dependencies: list of task_ids this depends on (can be empty)

Be practical and focus on backend operations. Consider error handling and retries in your planning."""

        user_prompt = f"""Goal: {goal}

{f"Context: {json.dumps(context, indent=2)}" if context else ""}

Generate a detailed task plan. Return ONLY valid JSON array, no markdown, no explanations."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            tasks = json.loads(content)
            
            # Validate and enhance tasks
            validated_tasks = []
            for i, task in enumerate(tasks):
                if "task_id" not in task:
                    task["task_id"] = f"task_{i+1}"
                if "dependencies" not in task:
                    task["dependencies"] = []
                validated_tasks.append(task)
            
            self.logger.info("Workflow planned", task_count=len(validated_tasks))
            return validated_tasks
            
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse planning response", error=str(e), response=content)
            raise ValueError(f"Invalid JSON response from planner: {e}")
        except Exception as e:
            self.logger.error("Planning failed", error=str(e))
            raise
    
    async def decide_next_tasks(
        self,
        state: Dict[str, Any],
        available_tasks: List[str]
    ) -> List[str]:
        """
        Decide which tasks to execute next based on current state.
        
        Args:
            state: Current workflow state
            available_tasks: List of task IDs that could be executed
            
        Returns:
            List of task IDs to execute next
        """
        if not available_tasks:
            return []
        
        # Simple dependency-based selection
        # In production, this could use LLM for more intelligent decision-making
        completed = set(state.get("completed_tasks", []))
        failed = set(state.get("failed_tasks", []))
        
        next_tasks = []
        for task_id in available_tasks:
            task = state["tasks"].get(task_id, {})
            dependencies = task.get("dependencies", [])
            
            # Check if all dependencies are completed
            if all(dep in completed for dep in dependencies):
                if task_id not in completed and task_id not in failed:
                    next_tasks.append(task_id)
        
        return next_tasks
    
    async def optimize_plan(
        self,
        original_plan: List[Dict[str, Any]],
        execution_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Optimize the plan based on execution history.
        
        Args:
            original_plan: Original task plan
            execution_history: History of task executions
            
        Returns:
            Optimized task plan
        """
        # For now, return original plan
        # In production, analyze history and suggest optimizations
        return original_plan

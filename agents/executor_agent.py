"""Executor agent that handles task execution with reasoning."""
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import structlog

from config import settings
from core.executor import ActionExecutor

logger = structlog.get_logger()


class ExecutorAgent:
    """Agent responsible for executing tasks with reasoning."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,  # Low temperature for consistent execution
            api_key=settings.openai_api_key
        )
        self.executor = ActionExecutor()
        self.logger = logger.bind(component="ExecutorAgent")
    
    async def execute_task(
        self,
        task: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task with reasoning and error handling.
        
        Args:
            task: Task to execute
            state: Current workflow state
            
        Returns:
            Execution result with status and data
        """
        task_id = task["task_id"]
        self.logger.info("Executing task", task_id=task_id, task_name=task.get("name"))
        
        # Use LLM to reason about execution if needed
        should_reason = task.get("action_config", {}).get("require_reasoning", False)
        
        if should_reason:
            reasoning = await self._reason_about_task(task, state)
            self.logger.info("Task reasoning", task_id=task_id, reasoning=reasoning)
        
        # Execute the action
        action_type = task["action_type"]
        action_config = task["action_config"]
        
        try:
            result = await self.executor.execute(action_type, action_config)
            
            if result["status"] == "error":
                return {
                    "status": "failed",
                    "error": result.get("error", "Unknown error"),
                    "data": None
                }
            
            return {
                "status": "success",
                "data": result["data"],
                "error": None
            }
            
        except Exception as e:
            self.logger.error("Task execution exception", task_id=task_id, error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "data": None
            }
    
    async def _reason_about_task(
        self,
        task: Dict[str, Any],
        state: Dict[str, Any]
    ) -> str:
        """Use LLM to reason about task execution."""
        system_prompt = """You are an execution reasoning agent. Analyze the task and current state to determine the best approach for execution."""
        
        user_prompt = f"""Task: {task.get('name')}
Description: {task.get('description')}
Action Type: {task.get('action_type')}
Action Config: {task.get('action_config')}

Current State:
- Completed tasks: {state.get('completed_tasks', [])}
- Memory: {state.get('memory', {})}

Provide reasoning about how to execute this task effectively."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            self.logger.warning("Reasoning failed", error=str(e))
            return "Reasoning unavailable"
    
    async def handle_failure(
        self,
        task: Dict[str, Any],
        error: str,
        state: Dict[str, Any],
        retry_count: int
    ) -> Dict[str, Any]:
        """
        Decide how to handle task failure.
        
        Args:
            task: Failed task
            error: Error message
            state: Current workflow state
            retry_count: Number of retries attempted
            
        Returns:
            Decision dict with action (retry, skip, fail_workflow, modify)
        """
        max_retries = state.get("context", {}).get("metadata", {}).get("max_retries", 3)
        
        if retry_count >= max_retries:
            return {
                "action": "fail_workflow",
                "reason": f"Max retries ({max_retries}) exceeded"
            }
        
        # Use LLM to decide on retry strategy
        system_prompt = """You are a failure recovery agent. Analyze task failures and decide the best recovery strategy."""
        
        user_prompt = f"""Task failed: {task.get('name')}
Error: {error}
Retry count: {retry_count}/{max_retries}
Task config: {task.get('action_config')}

Should we:
1. Retry the task (if error seems transient)
2. Skip the task (if it's not critical)
3. Modify the task config and retry (if config issue)
4. Fail the entire workflow (if critical failure)

Respond with JSON: {{"action": "retry|skip|modify|fail_workflow", "reason": "explanation", "modifications": {{}} if modify}}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            # Parse JSON response
            import json
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            decision = json.loads(content)
            return decision
            
        except Exception as e:
            self.logger.warning("Failure handling decision failed", error=str(e))
            # Default to retry if we can't decide
            return {
                "action": "retry" if retry_count < max_retries else "fail_workflow",
                "reason": "Default decision"
            }

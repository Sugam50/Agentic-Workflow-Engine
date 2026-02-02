"""API orchestration workflow example."""
from typing import Dict, Any, List
from core.engine import WorkflowEngine


class APIOrchestrationWorkflow:
    """Example workflow for orchestrating multiple API calls."""
    
    def __init__(self):
        self.engine = WorkflowEngine()
    
    async def run(
        self,
        api_calls: List[Dict[str, Any]],
        orchestration_strategy: str = "sequential"
    ) -> Dict[str, Any]:
        """
        Run an API orchestration workflow.
        
        Args:
            api_calls: List of API call configurations
            orchestration_strategy: 'sequential', 'parallel', or 'conditional'
            
        Returns:
            Workflow execution result
        """
        api_descriptions = "\n".join([
            f"- {call.get('name', 'API call')}: {call.get('method', 'GET')} {call.get('url')}"
            for call in api_calls
        ])
        
        goal = f"""Orchestrate the following API calls using {orchestration_strategy} strategy:
{api_descriptions}

Handle rate limiting, retries, and data dependencies between calls. Aggregate results appropriately."""
        
        config = {
            "workflow_type": "api_orchestration",
            "api_calls": api_calls,
            "orchestration_strategy": orchestration_strategy,
            "max_retries": 3
        }
        
        return await self.engine.run(goal, config=config)

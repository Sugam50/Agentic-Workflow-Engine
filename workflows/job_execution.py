"""Background job execution and monitoring workflow example."""
from typing import Dict, Any
from core.engine import WorkflowEngine


class JobExecutionWorkflow:
    """Example workflow for background job execution and monitoring."""
    
    def __init__(self):
        self.engine = WorkflowEngine()
    
    async def run(
        self,
        job_config: Dict[str, Any],
        monitor_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Run a job execution workflow with monitoring.
        
        Args:
            job_config: Job configuration (type, parameters, etc.)
            monitor_interval: Seconds between monitoring checks
            
        Returns:
            Workflow execution result
        """
        job_type = job_config.get("type", "generic")
        job_params = job_config.get("parameters", {})
        
        goal = f"""Execute a {job_type} background job with the following parameters: {job_params}.
        Monitor the job execution, handle failures, and provide status updates. Ensure proper 
        cleanup and resource management."""
        
        config = {
            "workflow_type": "job_execution",
            "job_config": job_config,
            "monitor_interval": monitor_interval,
            "max_retries": 3
        }
        
        return await self.engine.run(goal, config=config)

"""Data ingestion and transformation pipeline workflow example."""
from typing import Dict, Any
from core.engine import WorkflowEngine


class DataPipelineWorkflow:
    """Example workflow for data ingestion and transformation."""
    
    def __init__(self):
        self.engine = WorkflowEngine()
    
    async def run(
        self,
        source_url: str,
        destination_path: str,
        transformations: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run a data pipeline workflow.
        
        Args:
            source_url: URL to fetch data from
            destination_path: Path to save transformed data
            transformations: Optional transformation configuration
            
        Returns:
            Workflow execution result
        """
        goal = f"""Ingest data from {source_url}, transform it according to business rules, 
        and save the result to {destination_path}. Handle errors gracefully and ensure 
        data quality."""
        
        config = {
            "workflow_type": "data_pipeline",
            "source_url": source_url,
            "destination_path": destination_path,
            "transformations": transformations or {},
            "max_retries": 3
        }
        
        return await self.engine.run(goal, config=config)

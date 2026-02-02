"""Main entry point for the Agentic Workflow Engine."""
import asyncio
import argparse
from pathlib import Path
import sys

from utils.logger import setup_logging
from utils.observability import WorkflowObserver
from core.engine import WorkflowEngine
from workflows.data_pipeline import DataPipelineWorkflow
from workflows.api_orchestration import APIOrchestrationWorkflow
from workflows.job_execution import JobExecutionWorkflow


async def run_custom_workflow(goal: str, workflow_id: str = None):
    """Run a custom workflow from a goal description."""
    setup_logging()
    observer = WorkflowObserver()
    
    engine = WorkflowEngine()
    result = await engine.run(goal, workflow_id=workflow_id)
    
    # Get final state
    final_state = result if isinstance(result, dict) else result.get("complete", {})
    
    # Save and display results
    observer.save_state(
        final_state["context"]["workflow_id"],
        final_state
    )
    observer.print_summary(final_state)
    
    return final_state


async def run_data_pipeline_example():
    """Example: Data pipeline workflow."""
    print("Running Data Pipeline Workflow Example...")
    
    workflow = DataPipelineWorkflow()
    result = await workflow.run(
        source_url="https://jsonplaceholder.typicode.com/posts",
        destination_path="output/transformed_data.json",
        transformations={"format": "json", "filter": "userId==1"}
    )
    
    return result


async def run_api_orchestration_example():
    """Example: API orchestration workflow."""
    print("Running API Orchestration Workflow Example...")
    
    workflow = APIOrchestrationWorkflow()
    result = await workflow.run(
        api_calls=[
            {
                "name": "Get Users",
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/users"
            },
            {
                "name": "Get Posts",
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/posts",
                "depends_on": ["Get Users"]
            }
        ],
        orchestration_strategy="sequential"
    )
    
    return result


async def run_job_execution_example():
    """Example: Job execution workflow."""
    print("Running Job Execution Workflow Example...")
    
    workflow = JobExecutionWorkflow()
    result = await workflow.run(
        job_config={
            "type": "data_processing",
            "parameters": {
                "input_file": "data/input.csv",
                "output_file": "data/output.csv",
                "operations": ["clean", "transform", "validate"]
            }
        },
        monitor_interval=5
    )
    
    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agentic Workflow Engine - Autonomous workflow execution"
    )
    parser.add_argument(
        "--goal",
        type=str,
        help="High-level goal description for custom workflow"
    )
    parser.add_argument(
        "--workflow-id",
        type=str,
        help="Optional workflow ID"
    )
    parser.add_argument(
        "--example",
        type=str,
        choices=["data_pipeline", "api_orchestration", "job_execution"],
        help="Run an example workflow"
    )
    
    args = parser.parse_args()
    
    if args.example:
        setup_logging()
        observer = WorkflowObserver()
        
        if args.example == "data_pipeline":
            result = asyncio.run(run_data_pipeline_example())
        elif args.example == "api_orchestration":
            result = asyncio.run(run_api_orchestration_example())
        elif args.example == "job_execution":
            result = asyncio.run(run_job_execution_example())
        
        # Display results
        if isinstance(result, dict) and "context" in result:
            observer.print_summary(result)
        else:
            print("Workflow completed. Check logs for details.")
    
    elif args.goal:
        result = asyncio.run(run_custom_workflow(args.goal, args.workflow_id))
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python main.py --goal 'Fetch data from API and save to file'")
        print("  python main.py --example data_pipeline")
        print("  python main.py --example api_orchestration")
        print("  python main.py --example job_execution")


if __name__ == "__main__":
    main()

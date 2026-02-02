"""Observability utilities for workflow monitoring."""
from typing import Dict, Any, List
from datetime import datetime
import json
from pathlib import Path


class WorkflowObserver:
    """Observer for workflow execution monitoring."""
    
    def __init__(self, output_dir: str = "workflow_state"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_state(self, workflow_id: str, state: Dict[str, Any]):
        """Save workflow state to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{workflow_id}_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(state, f, indent=2, default=str)
    
    def get_metrics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from workflow state."""
        tasks = state.get("tasks", {})
        completed = state.get("completed_tasks", [])
        failed = state.get("failed_tasks", [])
        
        total_tasks = len(tasks)
        completed_count = len(completed)
        failed_count = len(failed)
        
        # Calculate task durations
        task_durations = []
        for task_id, task in tasks.items():
            if task.get("started_at") and task.get("completed_at"):
                started = datetime.fromisoformat(task["started_at"]) if isinstance(task["started_at"], str) else task["started_at"]
                completed = datetime.fromisoformat(task["completed_at"]) if isinstance(task["completed_at"], str) else task["completed_at"]
                duration = (completed - started).total_seconds()
                task_durations.append(duration)
        
        avg_duration = sum(task_durations) / len(task_durations) if task_durations else 0
        total_duration = sum(task_durations)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "success_rate": completed_count / total_tasks if total_tasks > 0 else 0,
            "average_task_duration_seconds": avg_duration,
            "total_duration_seconds": total_duration,
            "retry_count": sum(task.get("retry_count", 0) for task in tasks.values()),
        }
    
    def print_summary(self, state: Dict[str, Any]):
        """Print a human-readable workflow summary."""
        context = state.get("context", {})
        metrics = self.get_metrics(state)
        
        print("\n" + "="*60)
        print("WORKFLOW EXECUTION SUMMARY")
        print("="*60)
        print(f"Workflow ID: {context.get('workflow_id')}")
        print(f"Goal: {context.get('goal')}")
        print(f"Status: {context.get('status')}")
        print(f"Started: {context.get('started_at')}")
        print(f"Completed: {context.get('completed_at')}")
        print("\nMetrics:")
        print(f"  Total Tasks: {metrics['total_tasks']}")
        print(f"  Completed: {metrics['completed_tasks']}")
        print(f"  Failed: {metrics['failed_tasks']}")
        print(f"  Success Rate: {metrics['success_rate']:.2%}")
        print(f"  Average Task Duration: {metrics['average_task_duration_seconds']:.2f}s")
        print(f"  Total Duration: {metrics['total_duration_seconds']:.2f}s")
        print(f"  Total Retries: {metrics['retry_count']}")
        
        if state.get("errors"):
            print("\nErrors:")
            for error in state["errors"]:
                print(f"  - {error.get('step')}: {error.get('error')}")
        
        print("="*60 + "\n")

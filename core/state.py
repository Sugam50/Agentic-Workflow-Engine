"""State management for workflow execution."""
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime
from enum import Enum
import json


class TaskStatus(str, Enum):
    """Status of a workflow task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class WorkflowContext(TypedDict):
    """Context information for workflow execution."""
    workflow_id: str
    goal: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    metadata: Dict[str, Any]


class Task(TypedDict):
    """Represents a single task in the workflow."""
    task_id: str
    name: str
    description: str
    action_type: str
    action_config: Dict[str, Any]
    status: TaskStatus
    dependencies: List[str]
    retry_count: int
    error: Optional[str]
    result: Optional[Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class WorkflowState(TypedDict):
    """State of the workflow execution graph."""
    context: WorkflowContext
    tasks: Dict[str, Task]
    execution_history: List[Dict[str, Any]]
    current_task: Optional[str]
    memory: Dict[str, Any]
    errors: List[Dict[str, Any]]
    next_tasks: List[str]
    completed_tasks: List[str]
    failed_tasks: List[str]


def workflow_state_to_dict(state: WorkflowState) -> Dict[str, Any]:
    """Convert state to dictionary for serialization."""
    return {
        "context": {
            **state["context"],
            "started_at": state["context"]["started_at"].isoformat() if isinstance(state["context"]["started_at"], datetime) else state["context"]["started_at"],
            "completed_at": state["context"]["completed_at"].isoformat() if isinstance(state["context"]["completed_at"], datetime) else state["context"]["completed_at"],
        },
        "tasks": {
            k: {
                **v,
                "status": v["status"].value if isinstance(v["status"], TaskStatus) else v["status"],
                "started_at": v["started_at"].isoformat() if isinstance(v["started_at"], datetime) else v["started_at"],
                "completed_at": v["completed_at"].isoformat() if isinstance(v["completed_at"], datetime) else v["completed_at"],
            }
            for k, v in state["tasks"].items()
        },
        "execution_history": state["execution_history"],
        "current_task": state["current_task"],
        "memory": state["memory"],
        "errors": state["errors"],
        "next_tasks": state["next_tasks"],
        "completed_tasks": state["completed_tasks"],
        "failed_tasks": state["failed_tasks"],
    }


def create_initial_state(workflow_id: str, goal: str) -> WorkflowState:
    """Create initial workflow state."""
    return {
        "context": {
            "workflow_id": workflow_id,
            "goal": goal,
            "started_at": datetime.now(),
            "completed_at": None,
            "status": "running",
            "metadata": {},
        },
        "tasks": {},
        "execution_history": [],
        "current_task": None,
        "memory": {},
        "errors": [],
        "next_tasks": [],
        "completed_tasks": [],
        "failed_tasks": [],
    }

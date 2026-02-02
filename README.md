# Agentic Workflow Engine

An autonomous workflow execution engine that uses LangGraph and OpenAI APIs to plan, reason, and execute multi-step backend workflows without human intervention.

## Overview

The Agentic Workflow Engine is a production-ready system that:

- **Autonomously plans** complex workflows by breaking down high-level goals into executable steps
- **Dynamically decides** task execution order based on context and state
- **Coordinates multiple agents** using LangGraph's stateful graph execution model
- **Handles failures intelligently** with retries, error recovery, and branching logic
- **Executes real backend actions** including API calls, database operations, file processing, and async jobs
- **Maintains memory/state** across steps for consistent decision-making
- **Provides observability** through structured logging, metrics, and state inspection

## Features

### Core Capabilities

- **Goal-Driven Planning**: LLM-powered task decomposition from natural language goals
- **Stateful Execution**: LangGraph-based workflow orchestration with persistent state
- **Intelligent Retry Logic**: Context-aware failure handling with configurable retry strategies
- **Backend Action Execution**: Support for HTTP APIs, database queries, file operations, and data transformations
- **Memory Management**: Persistent context and state across workflow steps
- **Observability**: Comprehensive logging, metrics, and execution history

### Supported Action Types

- **API Calls**: HTTP requests (GET, POST, PUT, DELETE) with retry logic
- **Database Queries**: SQL query execution (PostgreSQL support)
- **File Operations**: Read, write, delete, and list file operations
- **Data Transformations**: JSON parsing, mapping, and data manipulation
- **Wait/Delay**: Configurable delays for rate limiting or coordination

## Installation

### Prerequisites

- Python 3.9+
- OpenAI API key
- (Optional) PostgreSQL database for DB operations
- (Optional) Redis for state caching

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd "Agentic Workflow Engine"
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: `gpt-4-turbo-preview`)
- `DATABASE_URL`: PostgreSQL connection string (optional)
- `REDIS_URL`: Redis connection string (optional)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Usage

### Command Line Interface

Run a custom workflow from a goal description:
```bash
python main.py --goal "Fetch data from https://api.example.com/users and save to output/users.json"
```

Run example workflows:
```bash
# Data pipeline workflow
python main.py --example data_pipeline

# API orchestration workflow
python main.py --example api_orchestration

# Job execution workflow
python main.py --example job_execution
```

### Programmatic Usage

```python
from core.engine import WorkflowEngine
import asyncio

async def main():
    engine = WorkflowEngine()
    
    result = await engine.run(
        goal="Process user data from API and store in database",
        workflow_id="my-workflow-123"
    )
    
    print(f"Workflow status: {result['context']['status']}")
    print(f"Completed tasks: {len(result['completed_tasks'])}")

asyncio.run(main())
```

### Using Pre-built Workflows

```python
from workflows.data_pipeline import DataPipelineWorkflow
import asyncio

async def main():
    workflow = DataPipelineWorkflow()
    result = await workflow.run(
        source_url="https://jsonplaceholder.typicode.com/posts",
        destination_path="output/transformed_data.json",
        transformations={"format": "json", "filter": "userId==1"}
    )
    print(result)

asyncio.run(main())
```

## Architecture

### Core Components

```
core/
├── engine.py          # Main workflow engine (LangGraph orchestration)
├── state.py           # State management and TypedDict definitions
└── executor.py        # Backend action executor

agents/
├── planner.py         # Planning agent (task decomposition)
└── executor_agent.py  # Execution agent (task execution with reasoning)

workflows/
├── data_pipeline.py       # Data ingestion/transformation example
├── api_orchestration.py   # API orchestration example
└── job_execution.py       # Background job execution example

utils/
├── logger.py          # Structured logging setup
└── observability.py   # Metrics and state inspection
```

### Workflow Execution Flow

1. **Planning Phase**: Planning agent breaks down goal into tasks
2. **Decision Phase**: System determines which tasks can execute (dependency resolution)
3. **Execution Phase**: Executor agent runs tasks with error handling
4. **Failure Handling**: Failed tasks are analyzed and retried/skipped as appropriate
5. **Completion**: Final state is collected and metrics are generated

### State Management

The workflow state includes:
- **Context**: Workflow metadata, goal, status, timestamps
- **Tasks**: Task definitions with status, dependencies, results
- **Memory**: Persistent data shared across tasks
- **Execution History**: Complete log of task executions
- **Error Tracking**: Failed tasks and error details

## Example Workflows

### Data Pipeline

Ingest data from a source, transform it, and save to destination:

```python
from workflows.data_pipeline import DataPipelineWorkflow

workflow = DataPipelineWorkflow()
result = await workflow.run(
    source_url="https://api.example.com/data",
    destination_path="output/processed.json",
    transformations={"format": "json", "validate": True}
)
```

### API Orchestration

Coordinate multiple API calls with dependencies:

```python
from workflows.api_orchestration import APIOrchestrationWorkflow

workflow = APIOrchestrationWorkflow()
result = await workflow.run(
    api_calls=[
        {"name": "Auth", "method": "POST", "url": "https://api.example.com/auth"},
        {"name": "GetData", "method": "GET", "url": "https://api.example.com/data", 
         "depends_on": ["Auth"]}
    ],
    orchestration_strategy="sequential"
)
```

### Job Execution

Execute and monitor background jobs:

```python
from workflows.job_execution import JobExecutionWorkflow

workflow = JobExecutionWorkflow()
result = await workflow.run(
    job_config={
        "type": "data_processing",
        "parameters": {"input": "data.csv", "output": "result.csv"}
    },
    monitor_interval=5
)
```

## Configuration

### Workflow Configuration

Configure workflow behavior via the `config` parameter:

```python
result = await engine.run(
    goal="...",
    config={
        "max_retries": 3,
        "workflow_type": "custom",
        "custom_metadata": {...}
    }
)
```

### Action Configuration

Tasks support various action configurations:

**API Call:**
```json
{
  "action_type": "api_call",
  "action_config": {
    "method": "POST",
    "url": "https://api.example.com/endpoint",
    "headers": {"Authorization": "Bearer token"},
    "body": {"key": "value"},
    "timeout": 30
  }
}
```

**File Operation:**
```json
{
  "action_type": "file_operation",
  "action_config": {
    "operation": "write",
    "path": "output/data.json",
    "content": "{\"key\": \"value\"}"
  }
}
```

## Observability

### Logging

Structured logging is configured via `structlog`:

```python
from utils.logger import setup_logging
setup_logging()
```

Logs include:
- Workflow execution progress
- Task execution details
- Error messages and stack traces
- Performance metrics

### Metrics

Extract metrics from workflow state:

```python
from utils.observability import WorkflowObserver

observer = WorkflowObserver()
metrics = observer.get_metrics(result)
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Average task duration: {metrics['average_task_duration_seconds']:.2f}s")
```

### State Inspection

Save and inspect workflow state:

```python
observer = WorkflowObserver()
observer.save_state(workflow_id, result)
observer.print_summary(result)
```

## Error Handling

The engine implements intelligent error handling:

1. **Automatic Retries**: Failed tasks are retried with exponential backoff
2. **LLM-Powered Recovery**: The executor agent analyzes failures and decides recovery strategy
3. **Graceful Degradation**: Non-critical tasks can be skipped
4. **Workflow-Level Failure**: Critical failures can fail the entire workflow

Retry strategies:
- **Retry**: Task is retried with same or modified configuration
- **Skip**: Task is skipped (for non-critical operations)
- **Modify**: Task configuration is modified before retry
- **Fail Workflow**: Entire workflow is marked as failed

## Extensibility

### Adding Custom Actions

Extend `ActionExecutor` to add custom action types:

```python
from core.executor import ActionExecutor

class CustomExecutor(ActionExecutor):
    async def _execute_custom_action(self, config):
        # Your custom logic
        return {"status": "success", "data": {...}}

    async def execute(self, action_type, config):
        if action_type == "custom_action":
            return await self._execute_custom_action(config)
        return await super().execute(action_type, config)
```

### Custom Workflows

Create custom workflow classes:

```python
from core.engine import WorkflowEngine

class MyCustomWorkflow:
    def __init__(self):
        self.engine = WorkflowEngine()
    
    async def run(self, **kwargs):
        goal = self._build_goal(**kwargs)
        return await self.engine.run(goal)
```

## Best Practices

1. **Clear Goals**: Provide specific, actionable goal descriptions
2. **Error Handling**: Configure appropriate retry limits and strategies
3. **Monitoring**: Use observability tools to track workflow execution
4. **State Management**: Leverage memory for cross-task data sharing
5. **Testing**: Test workflows with small goals before scaling up

## Limitations

- Database operations require proper driver setup (currently placeholder)
- Parallel task execution is limited (tasks execute sequentially)
- LLM API costs can accumulate with complex workflows
- State persistence uses in-memory storage (can be extended to Redis/DB)

## Roadmap

- [ ] Parallel task execution support
- [ ] Database driver integration (asyncpg, SQLAlchemy async)
- [ ] Redis-based state persistence
- [ ] Web UI for workflow monitoring
- [ ] Workflow templates and library
- [ ] Advanced scheduling and cron support
- [ ] Workflow versioning and rollback

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Specify your license here]

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [OpenAI](https://openai.com/)
- Uses [LangChain](https://github.com/langchain-ai/langchain) for LLM integration

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: This is a production-focused implementation emphasizing deterministic execution, observability, and extensibility over toy demos.

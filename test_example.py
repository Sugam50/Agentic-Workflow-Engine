"""Simple test script to verify the workflow engine setup."""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils.logger import setup_logging
from core.engine import WorkflowEngine
from utils.observability import WorkflowObserver


async def test_simple_workflow():
    """Test a simple workflow execution."""
    setup_logging()
    observer = WorkflowObserver()
    
    print("Testing Agentic Workflow Engine...")
    print("=" * 60)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment variables")
        print("Please set it in your .env file or environment")
        return
    
    engine = WorkflowEngine()
    
    # Simple test goal
    goal = "Create a file called 'test_output.txt' with the content 'Hello from Agentic Workflow Engine!'"
    
    print(f"Goal: {goal}")
    print("\nExecuting workflow...\n")
    
    try:
        result = await engine.run(goal)
        
        # Display results
        observer.print_summary(result)
        
        # Check if file was created
        from pathlib import Path
        test_file = Path("test_output.txt")
        if test_file.exists():
            print(f"✓ Test file created successfully!")
            print(f"  Content: {test_file.read_text()}")
        else:
            print("⚠ Test file not found (workflow may have failed or used different path)")
        
        print("\n" + "=" * 60)
        print("Test completed!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple_workflow())

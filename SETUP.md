# Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4-turbo-preview
   LOG_LEVEL=INFO
   ```

3. **Test Installation**
   ```bash
   python test_example.py
   ```

## Environment Variables

### Required
- `OPENAI_API_KEY`: Your OpenAI API key (get one at https://platform.openai.com/)

### Optional
- `OPENAI_MODEL`: Model to use (default: `gpt-4-turbo-preview`)
- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/db`)
- `REDIS_URL`: Redis connection string (e.g., `redis://localhost:6379/0`)
- `LOG_LEVEL`: Logging level - `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)

## Verification

Run the test script to verify everything is working:
```bash
python test_example.py
```

This will:
1. Check if your OpenAI API key is configured
2. Run a simple workflow (creating a test file)
3. Display execution summary and metrics

## Troubleshooting

### Import Errors
If you see import errors, make sure:
- Virtual environment is activated
- All dependencies are installed: `pip install -r requirements.txt`
- You're running from the project root directory

### OpenAI API Errors
- Verify your API key is correct
- Check your OpenAI account has credits/quota
- Ensure the model name is valid (e.g., `gpt-4-turbo-preview`)

### Module Not Found
If Python can't find modules:
- Make sure you're in the project root
- Check that `__init__.py` files exist in all package directories
- Try: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

## Next Steps

- Read the [README.md](README.md) for detailed usage
- Try example workflows: `python main.py --example data_pipeline`
- Create your own workflows using the API

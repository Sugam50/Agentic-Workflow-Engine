"""Action executor for backend operations."""
from typing import Any, Dict, Optional
import httpx
import aiohttp
import json
import structlog
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = structlog.get_logger()


class ActionExecutor:
    """Executes various backend actions."""
    
    def __init__(self):
        self.logger = logger.bind(component="ActionExecutor")
    
    async def execute(self, action_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action based on type and configuration.
        
        Args:
            action_type: Type of action (api_call, db_query, file_operation, etc.)
            config: Action-specific configuration
            
        Returns:
            Result dictionary with status and data
        """
        self.logger.info("Executing action", action_type=action_type, config=config)
        
        try:
            if action_type == "api_call":
                return await self._execute_api_call(config)
            elif action_type == "db_query":
                return await self._execute_db_query(config)
            elif action_type == "file_operation":
                return await self._execute_file_operation(config)
            elif action_type == "transform_data":
                return await self._execute_transform(config)
            elif action_type == "wait":
                return await self._execute_wait(config)
            else:
                raise ValueError(f"Unknown action type: {action_type}")
        except Exception as e:
            self.logger.error("Action execution failed", error=str(e), action_type=action_type)
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _execute_api_call(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an HTTP API call."""
        method = config.get("method", "GET").upper()
        url = config["url"]
        headers = config.get("headers", {})
        params = config.get("params", {})
        body = config.get("body")
        timeout = config.get("timeout", 30)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=body)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=body)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except:
                data = response.text
            
            return {
                "status": "success",
                "data": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": data
                }
            }
    
    async def _execute_db_query(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a database query."""
        if not settings.database_url:
            raise ValueError("Database URL not configured")
        
        # This is a placeholder - in production, use proper async DB driver
        query = config["query"]
        params = config.get("params", {})
        
        # For now, return a mock response
        # In production, implement actual database connection
        self.logger.warning("DB query execution not fully implemented", query=query)
        
        return {
            "status": "success",
            "data": {
                "query": query,
                "params": params,
                "rows": [],
                "note": "DB execution requires database driver setup"
            }
        }
    
    async def _execute_file_operation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operations."""
        operation = config["operation"]  # read, write, delete, list
        path = Path(config["path"])
        
        if operation == "read":
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            content = path.read_text()
            return {
                "status": "success",
                "data": {"content": content, "path": str(path)}
            }
        
        elif operation == "write":
            content = config["content"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return {
                "status": "success",
                "data": {"path": str(path), "bytes_written": len(content)}
            }
        
        elif operation == "delete":
            if path.exists():
                path.unlink()
            return {
                "status": "success",
                "data": {"path": str(path), "deleted": True}
            }
        
        elif operation == "list":
            if path.is_dir():
                files = [f.name for f in path.iterdir()]
                return {
                    "status": "success",
                    "data": {"files": files, "path": str(path)}
                }
            else:
                raise ValueError(f"Path is not a directory: {path}")
        
        else:
            raise ValueError(f"Unknown file operation: {operation}")
    
    async def _execute_transform(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data transformation."""
        transform_type = config.get("type", "json")
        input_data = config["input"]
        
        if transform_type == "json":
            # Parse JSON if string, otherwise return as-is
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                except:
                    data = input_data
            else:
                data = input_data
            
            # Apply transformations if specified
            if "mapping" in config:
                mapping = config["mapping"]
                if isinstance(data, dict):
                    transformed = {mapping.get(k, k): v for k, v in data.items()}
                else:
                    transformed = data
            else:
                transformed = data
            
            return {
                "status": "success",
                "data": transformed
            }
        
        else:
            raise ValueError(f"Unknown transform type: {transform_type}")
    
    async def _execute_wait(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a wait/delay operation."""
        import asyncio
        duration = config.get("duration", 1.0)
        await asyncio.sleep(duration)
        
        return {
            "status": "success",
            "data": {"waited_seconds": duration}
        }

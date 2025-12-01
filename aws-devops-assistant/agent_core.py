import json
import boto3
import logging
import asyncio
from typing import List, Callable, Dict, Any, Optional, Union
from botocore.exceptions import ClientError

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BedrockAgent:
    """
    A production-ready wrapper around Amazon Bedrock for building AI agents.
    Supports both native Python tools and MCP servers.
    """

    def __init__(
        self,
        model_id: str,
        system_prompt: str,
        tools: List[Callable] = None,
        mcp_servers: List[StdioServerParameters] = None,
        region_name: str = "us-east-1"
    ):
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.mcp_servers = mcp_servers or []
        self.region_name = region_name
        
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        
        # We need to initialize tools. For MCP, this requires async.
        # Since this is a sync class, we will handle MCP discovery lazily or via a helper.
        self.tool_map = {tool.__name__: tool for tool in self.tools}
        self.native_tool_definitions = self._generate_native_tool_definitions()

    def _generate_native_tool_definitions(self) -> List[Dict[str, Any]]:
        """Generates Bedrock-compatible tool definitions from Python functions."""
        definitions = []
        for tool in self.tools:
            schema = getattr(tool, "_tool_schema", {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Input query"}
                    },
                    "required": ["query"]
                }
            })
            
            definitions.append({
                "toolSpec": {
                    "name": tool.__name__,
                    "description": tool.__doc__ or "No description provided.",
                    "inputSchema": schema
                }
            })
        return definitions

    def invoke(self, prompt: str) -> str:
        """
        Synchronous wrapper for the async invoke method.
        """
        return asyncio.run(self._invoke_async(prompt))

    async def _invoke_async(self, prompt: str) -> str:
        """
        Async invocation to handle MCP communication.
        """
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        
        # 1. Connect to MCP Servers and fetch tools
        mcp_tools = []
        active_mcp_sessions = []
        
        # Context managers for MCP clients
        exit_stack = []
        
        try:
            # Start MCP sessions
            for server_params in self.mcp_servers:
                # We manually manage the connection context here for simplicity in this loop
                # In a robust app, use AsyncExitStack
                transport = await stdio_client(server_params)
                read_stream, write_stream = transport
                session = ClientSession(read_stream, write_stream)
                await session.initialize()
                
                # List tools
                result = await session.list_tools()
                for tool in result.tools:
                    mcp_tools.append({
                        "toolSpec": {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                    })
                    # Map tool name to session for execution
                    self.tool_map[tool.name] = session
                
                active_mcp_sessions.append(session)

            # Combine definitions
            all_tool_definitions = self.native_tool_definitions + mcp_tools

            while True:
                # Basic inference configuration
                inference_config = {"temperature": 0.0}
                
                request_kwargs = {
                    "modelId": self.model_id,
                    "messages": messages,
                    "system": [{"text": self.system_prompt}],
                    "inferenceConfig": inference_config
                }
                
                if all_tool_definitions:
                    request_kwargs["toolConfig"] = {
                        "tools": all_tool_definitions
                    }

                # Call Bedrock 
                response = self.bedrock_runtime.converse(**request_kwargs)
                
                output_message = response['output']['message']
                messages.append(output_message)
                
                content = output_message['content']
                tool_use_requests = [c['toolUse'] for c in content if 'toolUse' in c]
                
                if not tool_use_requests:
                    text_blocks = [c['text'] for c in content if 'text' in c]
                    return "\n".join(text_blocks)
                
                # Execute tools
                tool_results = await self._execute_tools_async(tool_use_requests)
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

        except Exception as e:
            logger.error(f"Error during invocation: {e}")
            return f"Error: {e}"
        finally:
            
            pass

    async def _execute_tools_async(self, tool_requests: List[Dict]) -> List[Dict]:
        results = []
        for tool_use in tool_requests:
            tool_name = tool_use['name']
            tool_input = tool_use['input']
            tool_id = tool_use['toolUseId']
            
            logger.info(f"Executing tool: {tool_name}")
            
            handler = self.tool_map.get(tool_name)
            
            if isinstance(handler, ClientSession):
                # It's an MCP tool
                try:
                    mcp_result = await handler.call_tool(tool_name, arguments=tool_input)
                    # Extract text content from MCP result
                    content_text = "\n".join([c.text for c in mcp_result.content if c.type == 'text'])
                    result = content_text
                except Exception as e:
                    result = f"MCP Error: {e}"
            elif callable(handler):
                # It's a native Python tool
                try:
                    if 'query' in tool_input and len(tool_input) == 1:
                        result = handler(tool_input['query'])
                    else:
                        result = handler(**tool_input)
                except Exception as e:
                    result = f"Native Tool Error: {e}"
            else:
                result = f"Error: Tool {tool_name} not found."
            
            results.append({
                "toolResult": {
                    "toolUseId": tool_id,
                    "content": [{"text": str(result)}]
                }
            })
        return results

def tool(schema: Optional[Dict] = None):
    def decorator(func):
        if schema:
            func._tool_schema = schema
        return func
    return decorator

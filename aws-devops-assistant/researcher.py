from agent_core import BedrockAgent
from mcp import StdioServerParameters

def create_researcher_agent():
    # Define the MCP server connection
    # Note: This requires 'uv' to be installed on the system.
    # 'uvx' downloads and runs the MCP server package on the fly.
    aws_docs_server = StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server"]
    )

    return BedrockAgent(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        system_prompt="You are an AWS Researcher. Use the available tools to search AWS documentation.",
        mcp_servers=[aws_docs_server]
    )

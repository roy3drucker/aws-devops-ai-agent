import os
from agent_core import BedrockAgent, tool

@tool(schema={
    "json": {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Name of the file to write"},
            "content": {"type": "string", "description": "Content to write"}
        },
        "required": ["filename", "content"]
    }
})
def write_file(filename: str, content: str) -> str:
    """
    Writes content to a file.
    """
    try:
        with open(filename, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {filename}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool(schema={
    "json": {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Name of the file to read"}
        },
        "required": ["filename"]
    }
})
def read_file(filename: str) -> str:
    """
    Reads content from a file.
    """
    try:
        if not os.path.exists(filename):
            return "File not found."
        with open(filename, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def create_coder_agent():
    return BedrockAgent(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        system_prompt="You are a Coder Agent. You can read and write files.",
        tools=[write_file, read_file]
    )

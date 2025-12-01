from agent_core import BedrockAgent, tool
from alarm_manager import create_alarm_manager
from aws_manager import create_aws_manager
from coder import create_coder_agent
from researcher import create_researcher_agent

# --- Delegation Tools ---

@tool(schema={"json": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}})
def ask_alarm_manager(query: str) -> str:
    """Delegates a task to the Alarm Manager."""
    return create_alarm_manager().invoke(query)


@tool(schema={"json": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}})
def ask_aws_manager(query: str) -> str:
    """Delegates a task to the AWS Manager."""
    return create_aws_manager().invoke(query)


@tool(schema={"json": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}})
def ask_coder(query: str) -> str:
    """Delegates a task to the Coder Agent."""
    return create_coder_agent().invoke(query)


@tool(schema={"json": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}})
def ask_researcher(query: str) -> str:
    """Delegates a task to the Researcher Agent."""
    return create_researcher_agent().invoke(query)


# --- Orchestrator Factory ---

def create_orchestrator() -> BedrockAgent:
    """Creates the main Orchestrator agent."""
    
    system_prompt = """
    You are the **AWS DevOps Assistant Orchestrator**.
    You are the leader of a multi-agent team. Your goal is to solve complex DevOps tasks
    by delegating work to your specialized agents.

    ### Your Team:
    1. **Alarm Manager**: Monitors CloudWatch alarms and system health.
    2. **AWS Manager**: Executes infrastructure changes (EC2, DynamoDB).
    3. **Coder**: Handles file operations and script writing.
    4. **Researcher**: Provides AWS best practices and documentation lookups.

    ### Workflow:
    1. Analyze the user's request.
    2. Break it down into steps.
    3. Call the appropriate agent for each step.
    4. Synthesize the results and report back to the user.

    ### Example:
    User: "The website is down, please fix it."
    You:
    - Call `ask_alarm_manager` to check for errors.
    - If an error is found, call `ask_researcher` for a solution.
    - Call `ask_aws_manager` to implement the fix (e.g., restart server).
    """
    
    return BedrockAgent(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        system_prompt=system_prompt,
        tools=[
            ask_alarm_manager,
            ask_aws_manager,
            ask_coder,
            ask_researcher
        ]
    )

import boto3
from agent_core import BedrockAgent, tool

@tool(schema={
    "json": {
        "type": "object",
        "properties": {
            "state": {"type": "string", "enum": ["ALARM", "OK", "INSUFFICIENT_DATA"], "description": "Filter by alarm state"}
        }
    }
})
def check_alarms(state: str = "ALARM") -> str:
    """
    Lists CloudWatch alarms in the specified state.
    """
    cw = boto3.client('cloudwatch', region_name='us-east-1')
    try:
        response = cw.describe_alarms(StateValue=state)
        alarms = []
        for alarm in response['MetricAlarms']:
            alarms.append({
                "AlarmName": alarm['AlarmName'],
                "StateValue": alarm['StateValue'],
                "StateReason": alarm['StateReason'],
                "MetricName": alarm['MetricName']
            })
        return str(alarms) if alarms else "No alarms found in that state."
    except Exception as e:
        return f"Error checking alarms: {str(e)}"

def create_alarm_manager():
    return BedrockAgent(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        system_prompt="You are an Alarm Manager. Check CloudWatch alarms when asked.",
        tools=[check_alarms]
    )

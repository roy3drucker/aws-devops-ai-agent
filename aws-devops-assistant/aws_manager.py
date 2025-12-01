import boto3
from agent_core import BedrockAgent, tool

# --- Tool Definitions ---

@tool(schema={
    "json": {
        "type": "object",
        "properties": {
            "image_id": {
                "type": "string",
                "description": "AMI ID (e.g., ami-0c55b159cbfafe1f0)"
            },
            "instance_type": {
                "type": "string",
                "description": "Instance type (e.g., t2.micro)"
            },
            "subnet_id": {
                "type": "string",
                "description": "Optional: Subnet ID to launch in. If not provided, uses default."
            }
        },
        "required": ["image_id", "instance_type"]
    }
})
def launch_ec2_instance(image_id: str, instance_type: str, subnet_id: str = None) -> str:
    """
    Launches a single EC2 instance with the specified AMI and type.
    """
    ec2 = boto3.client('ec2', region_name='us-east-1')
    try:
        run_args = {
            'ImageId': image_id,
            'InstanceType': instance_type,
            'MinCount': 1,
            'MaxCount': 1
        }
        if subnet_id:
            run_args['SubnetId'] = subnet_id

        response = ec2.run_instances(**run_args)
        instance_id = response['Instances'][0]['InstanceId']
        return f"Success: Launched instance {instance_id}"
    except Exception as e:
        return f"Error launching instance: {str(e)}"


@tool(schema={
    "json": {
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the DynamoDB table"
            },
            "key_name": {
                "type": "string",
                "description": "Name of the primary key (Hash Key)"
            }
        },
        "required": ["table_name", "key_name"]
    }
})
def create_dynamodb_table(table_name: str, key_name: str) -> str:
    """
    Creates a DynamoDB table with On-Demand capacity.
    """
    dynamo = boto3.client('dynamodb', region_name='us-east-1')
    try:
        response = dynamo.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': key_name, 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': key_name, 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'  
        )
        status = response['TableDescription']['TableStatus']
        return f"Success: Table '{table_name}' creation started. Status: {status}"
    except Exception as e:
        return f"Error creating table: {str(e)}"


# --- Agent Factory ---

def create_aws_manager() -> BedrockAgent:
    """Creates and returns the AWS Manager agent."""
    return BedrockAgent(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        system_prompt=(
            "You are an AWS Manager Agent.\n"
            "Your responsibilities:\n"
            "1. Launch EC2 instances when requested.\n"
            "2. Create DynamoDB tables when requested.\n"
            "Always confirm the action before executing if parameters are unclear."
        ),
        tools=[launch_ec2_instance, create_dynamodb_table]
    )

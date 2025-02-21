import boto3
import os
import pytest
from moto import mock_aws

# Change the environment variables for testing purposes
@pytest.fixture(scope="session", autouse=True)
def aws_credentials():
    os.environ['AWS_ACCESS_KEY'] = "testing"
    os.environ['AWS_SECRET_KEY'] = "testing"
    os.environ['AWS_DEFAULT_REGION'] = "eu-north-1"

# Create a fake SQS client to use in our testing transactions
@pytest.fixture(scope="session")
def sqs_client(aws_credentials):
    with mock_aws():
        # Create a SQS client for the mocks
        client = boto3.client("sqs", region_name="eu-north-1")
        yield client

@pytest.fixture(scope="session", autouse=True)
def setup_sqs_queues(sqs_client, aws_credentials):
    with mock_aws():
        # Create queues for the mocks
        p1_url = sqs_client.create_queue(QueueName="p1Queue")["QueueUrl"]

        print(p1_url)

        # Set queues in our environment for testing
        os.environ["p1Queue_URL"] = p1_url

        yield

# Important, we want to load the app after we set the environment variables to avoid overwrite
# If app is magically loaded before setting environment variables, it causes issues with tests
@pytest.fixture(scope="session", autouse=True)
def load_app(setup_sqs_queues):
    from app import app
    return app
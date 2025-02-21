import threading
import pytest
import boto3
import os
from app import p1TeamsPush


@pytest.fixture
def client(load_app):
    with load_app.test_client() as client:
        yield client

def test_get_message_from_p1(client, setup_sqs_queues, monkeypatch, mocker):
    queue_url = os.environ["p1Queue_URL"]
    print(queue_url)
    # re patch the queue url after as we load the app as an import in the file
    monkeypatch.setattr("app.p1QueueURL", queue_url)

    # Patch teamswebhook so that it doesn't actually send a teams message
    mocker.patch("pymsteams.connectorcard.send", return_value=None)

    sqs_client = boto3.client("sqs", region_name="eu-north-1")

    message = {
        "title": "Pytest 2 Title",
        "description": "test description",
    }

    # Send message to the mock SQS queue
    sqs_client.send_message(QueueUrl = queue_url, MessageBody = str(message))

    thread = threading.Thread(target=p1TeamsPush)
    thread.start()
    thread.join(timeout=5)

    monkeypatch.setattr("app.stop_flag", True)
    thread.join()

    response = sqs_client.receive_message(QueueUrl = queue_url)
    assert "Messages" not in response



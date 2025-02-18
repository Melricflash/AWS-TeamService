from flask import Flask
import pymsteams
import boto3
from dotenv import load_dotenv
import os
import threading

load_dotenv()

# Entry point
app = Flask(__name__)

# Environment Variables
AWS_ACCESS = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION")
TEAMS_URL = os.getenv("TEAMS_WEBHOOK_URL")
p1QueueURL = os.getenv("p1Queue_URL")

# Create a SQS instance
sqs = boto3.client('sqs',
                   aws_access_key_id = AWS_ACCESS,
                   aws_secret_access_key = AWS_SECRET,
                   region_name = AWS_REGION # Move to environment later
                   )

stop_flag = False

@app.route("/")
def healthCheck():
    return "<h1> Healthy! </h1>"

# Function to retrieve messages from the P1 Queue and push to Teams
def p1TeamsPush():
    global stop_flag
    while not stop_flag:


            # Attempt to read from the queue
            response = sqs.receive_message(
                QueueUrl = p1QueueURL,
                MaxNumberOfMessages = 1,  # Just get one item from the queue for now
                WaitTimeSeconds = 2
            )

            if 'Messages' in response:
                # The contents of the message is stored in the body key of response
                # Also want to get the messageID to delete later
                queueMessage = response['Messages'][0]
                messageID = queueMessage['MessageId']
                receipt = queueMessage['ReceiptHandle']
                contents = queueMessage["Body"] # JSON string
                #print(contents)

                # eval turns this string into a dictionary - note not a good practice for user input
                parsedContents = eval(contents)

                title = parsedContents['title']
                #print(title)
                description = parsedContents['description']
                #print(description)

                # Make a teams message
                teamsMessage = pymsteams.connectorcard(TEAMS_URL)

                teamsMessage.title(title)
                teamsMessage.text(description)

                # Send the message to the channel
                teamsMessage.send()
                print("Message sent to teams...")

                # Delete from the queue, requires the receipt handle from before
                sqs.delete_message(QueueUrl = p1QueueURL, ReceiptHandle = receipt)
                print("Message deleted from SQS...")

            else:
                print("No messages found...")

def background_thread():
    sqs_thread = threading.Thread(target=p1TeamsPush, daemon=True)
    sqs_thread.start()
    return sqs_thread

bg_thread = background_thread()

# Need the name main stuff so that you can run the flask server without infinite loop of function
if __name__ == '__main__':
    # p1TeamsPush()
    try:
        app.run(host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("Shutting down...")
        stop_flag = True
        bg_thread.join()
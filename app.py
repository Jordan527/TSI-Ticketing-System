from flask import Flask, request, Response
import json
import boto3
import re
import os
from dotenv import load_dotenv

load_dotenv()

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

sqs_dlq_name = os.getenv("SQS_DLQ_NAME")
sqs_low_priority_name = os.getenv("SQS_LOW_PRIORITY_NAME")
sqs_medium_priority_name = os.getenv("SQS_MEDIUM_PRIORITY_NAME")
sqs_high_priority_name = os.getenv("SQS_HIGH_PRIORITY_NAME")

lambda_low_priority_name = os.getenv("LAMBDA_LOW_PRIORITY_NAME")
lambda_medium_priority_name = os.getenv("LAMBDA_MEDIUM_PRIORITY_NAME")
lambda_high_priority_name = os.getenv("LAMBDA_HIGH_PRIORITY_NAME")

s3_bucket_name = os.getenv("S3_BUCKET_NAME")

app = Flask(__name__)

@app.route("/", methods=["POST"])
def hook():
    raw = request.get_json()
    message = raw['text']
    message = re.sub(r'<\/?p>', '', message)
    pattern = re.compile(r'Title: (.*?)\nPriority: (.*?)\nDescription: (.*)', re.DOTALL | re.IGNORECASE)
    match = pattern.search(message)
    if not match:
        text = "Invalid format. Please use the following format:\n\nTitle: <title>\n\nPriority: <priority (Low, Medium or High)>\n\nDescription: <description>"
        return respond(text)
    
    if match.group(2).strip().lower() not in ["low", "medium", "high"]:
        text = "Invalid priority. Please use one of the following priorities: \n\nLow \n\nMedium \n\nHigh"
        return respond(text)

    
    title = match.group(1).strip()
    priority = match.group(2).strip().lower()
    description = match.group(3).strip()

    try:            
        match priority:
            case "low":
                sendToQueue({"title": title, "description": description}, sqs_low_priority_name)
            case "medium":
                sendToQueue({"title": title, "description": description}, sqs_medium_priority_name)
            case "high":
                sendToQueue({"title": title, "description": description}, sqs_high_priority_name)
        text = "Your ticket has been submitted successfully"
        return respond(text)
    except Exception as e:
        print(e)
        text = "There was an error processing your request"
        return respond(text)

def respond(text):
    payload = {
       "type":"message",
       "attachments":[
          {
             "contentType":"application/vnd.microsoft.card.adaptive",
             "content":{
                "$schema":"http://adaptivecards.io/schemas/adaptive-card.json",
                "type":"AdaptiveCard",
                "version":"1.2",
                "body":[
                    {
                    "type": "TextBlock",
                    "text": text,
                    "wrap": True
                    }
                ]
             }
          }
       ]
    }
    
    return Response(json.dumps(payload), status=200)

def sendToQueue(payload, sqsName):
    json_payload = json.dumps(payload)
    
    sqs = boto3.client("sqs")
    url = sqs.get_queue_by_name(QueueName=sqsName)["QueueUrl"]
    
    # queue_attributes = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=['QueueArn'])
        
    response = sqs.send_message( 
        QueueUrl=url, 
        DelaySeconds=10, 
        MessageBody=( 
            json_payload 
        ) 
    ) 

def initializeSQS():
    sqs = boto3.client("sqs")

    try:
        dql_url = sqs.get_queue_by_name(QueueName=sqs_dlq_name)["QueueUrl"]
    except:
        dql_url = sqs.create_queue(QueueName=sqs_dlq_name)["QueueUrl"]

    try:
        dlq_attributes = sqs.get_queue_attributes(QueueUrl=dql_url, AttributeNames=['QueueArn'])
        dlq_arn = dlq_attributes['Attributes']['QueueArn']

        redrive_policy = {
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': '3'
        }

        attributes = {
            'RedrivePolicy': json.dumps(redrive_policy)
        }

        try:
            sqs.get_queue_by_name(QueueName=sqs_low_priority_name)
        except:
            sqs.create_queue(QueueName=sqs_low_priority_name, Attributes=attributes)
        
        try:
            sqs.get_queue_by_name(QueueName=sqs_medium_priority_name)
        except:
            sqs.create_queue(QueueName=sqs_medium_priority_name, Attributes=attributes)

        try:
            sqs.get_queue_by_name(QueueName=sqs_high_priority_name)
        except:
            sqs.create_queue(QueueName=sqs_high_priority_name, Attributes=attributes)
    except Exception as e:
        shutdown(e)

def initialiseS3():
    s3 = boto3.client("s3")
    try:
        s3.create_bucket(Bucket=s3_bucket_name, CreateBucketConfiguration={'LocationConstraint': aws_region})
    except Exception as e:
        if "BucketAlreadyOwnedByYou" not in str(e):
            shutdown(e)

def shutdown(reason=""):
    if reason:
        print(reason)
    else:
        print("Error initializing resources")
    print("Shutting down")
    exit()
    

with app.app_context():
    boto3.setup_default_session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=aws_region)
    initializeSQS()
    initialiseS3()

if __name__ == "__main__":
    app.run()
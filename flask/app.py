from flask import Flask, request, Response
import json
import boto3
import re
import os
import zipfile
import inspect
import time
import requests
import logging

aws_region = ""

sqs_lp = ""
sqs_mp = ""
sqs_hp = ""

initialisation_error = False
exiting = False
error_reason = ""

app = Flask(__name__)

# Define the routes for the webhook
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

    initialiseBoto3()
    if initialisation_error:
        return Response(error_reason, status=200)

    create_global_variables()
    if initialisation_error:
        return Response(error_reason, status=200)

    
    title = match.group(1).strip()
    priority = match.group(2).strip().lower()
    description = match.group(3).strip()

    try:
        dict = {"Title": title, "Description": description}
        match priority:
            case "low":
                dict["Priority"] = "Low"
                sendToQueue(dict, sqs_lp)
            case "medium":
                dict["Priority"] = "Medium"
                sendToQueue(dict, sqs_mp)
            case "high":
                dict["Priority"] = "High"
                sendToQueue(dict, sqs_hp)
        text = "Your ticket has been submitted successfully"
        return respond(text)
    except Exception as e:
        print(e)
        text = "There was an error processing your request"
        return respond(text)

@app.route("/health", methods=["GET"])
def health():
    return Response("Healthy", status=200)


@app.after_request
def exit(response):
    global exiting
    if exiting:
        logging.error("Exiting")
        os._exit(1)
    return response

# Define the error handling function
def log_error(reason="", shutdown=False, initialisation=False):
    global error_reason
    if reason: 
        reason = "Error: " + str(reason)
    if not reason:
        reason = "Error initializing resources"
        
    error_reason = reason
    logging.error(reason)

    if initialisation:
        global initialisation_error
        initialisation_error = True

    if shutdown:
        global exiting
        exiting = True

def reset_error():
    global initialisation_error, exiting, error_reason
    initialisation_error = False
    exiting = False
    error_reason = ""

# Define the function to respond to the user
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

# Define the function to send a message to the queue
def sendToQueue(payload, sqsName):
    json_payload = json.dumps(payload)
    
    sqs = boto3.client("sqs")
    url = sqs.get_queue_url(QueueName=sqsName)["QueueUrl"]
        
    response = sqs.send_message( 
        QueueUrl=url, 
        DelaySeconds=10, 
        MessageBody=( 
            json_payload 
        ) 
    ) 

# Define the functions to initialise the resources
def initialiseLogging(logging_level=logging.INFO):
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename="data/app.log", level=logging_level, format="%(asctime)s - %(message)s")

def initialiseBoto3(old_region=None):
    global aws_region
    aws_region = str(os.environ.get("AWS_REGION"))
    aws_access_key_id = str(os.environ.get("AWS_ACCESS_KEY_ID"))
    aws_secret_access_key = str(os.environ.get("AWS_SECRET_ACCESS_KEY"))

    if "None" not in [aws_region, aws_access_key_id, aws_secret_access_key]:
        boto3.Session()
        boto3.setup_default_session(region_name=aws_region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    else:
        log_error("AWS credentials not found", shutdown=True, initialisation=True)

def create_global_variables(old_prefix=None):
    global sqs_lp, sqs_mp, sqs_hp

    sqs_lp = str(os.environ.get("SQS_LP"))
    sqs_mp = str(os.environ.get("SQS_MP"))
    sqs_hp = str(os.environ.get("SQS_HP"))

    if "None" in [sqs_lp, sqs_mp, sqs_hp]:
        log_error("Prefix not found", shutdown=True, initialisation=True)
        
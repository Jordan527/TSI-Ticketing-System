from flask import Flask, request, Response
import json
import boto3
import re

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
                sendToQueue({"title": title, "description": description}, "low-priority-queue")
            case "medium":
                sendToQueue({"title": title, "description": description}, "medium-priority-queue")
            case "high":
                sendToQueue({"title": title, "description": description}, "high-priority-queue")
        text = f"The following ticket has been created:\n\nTitle: {match.group(1)}\n\nPriority: {match.group(2)}\n\nDescription: {match.group(3)}"
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

def sendToQueue(payload, priority):
    json_payload = json.dumps(payload)
    
    sqs = boto3.client("sqs")
    try:
        url = sqs.get_queue_by_name(QueueName=priority)["QueueUrl"]
    except:
        url = sqs.create_queue(QueueName=priority)["QueueUrl"]
        
    response = sqs.send_message( 
        QueueUrl=url, 
        DelaySeconds=10, 
        MessageBody=( 
            json_payload 
        ) 
    ) 

if __name__ == "__main__":
    app.run()
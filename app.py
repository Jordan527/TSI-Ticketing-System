from flask import Flask, request, Response
import json
import boto3

app = Flask(__name__)

@app.route("/", methods=["POST"])
def hook():
    try:
        data = json.loads(request.data)
        if "title" not in data:
            return Response(status=400)
        
        title = data["title"].strip()
        priority = int(data["priority"])
        description = data["description"].strip()
        
        match priority:
            case 1:
                sendToQueue({"title": title, "description": description}, "high-priority-queue")
            case 2:
                sendToQueue({"title": title, "description": description}, "medium-priority-queue")
            case 3:
                sendToQueue({"title": title, "description": description}, "low-priority-queue")
        
        return Response("Your ticket has been sent", status=200)
    except Exception as e:
        return Response("There was an error processing your request", status=200)


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
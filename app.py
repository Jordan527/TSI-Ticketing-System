from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/", methods=["POST"])
def hook():
    data = json.loads(request.data)
    html = data["text"]
    html = html.replace("</p>", "")
    html = html.replace("<p>", "")
    lines = html.split("\r\n")
    lines.pop(0)
    dictionary = {}
    
    for line in lines:
        line = line.split(":")
        dictionary[line[0].strip().lower()] = line[1].strip()
    
    if not ("title" in dictionary and "priority" in dictionary and "description" in dictionary):
        return {
            "type": "message",
            "text": "<p>Please submit your ticket in the following format:</p> <p>Title: </p> <p>Priority: </p> <p>Description: </p>"
        }
        
    match dictionary["priority"].lower():
        case "low":
            return {
                "type": "message",
                "text": "Low priority ticket submitted!"
            }
        case "medium":
            return {
                "type": "message",
                "text": "Medium priority ticket submitted!"
            }
        case "high":
            return {
                "type": "message",
                "text": "High priority ticket submitted!"
            }
        case _:
            return {
                "type": "message",
                "text": "Invalid priority level! Please submit a ticket with a priority level of low, medium or high."
            }

if __name__ == "__main__":
    app.run()
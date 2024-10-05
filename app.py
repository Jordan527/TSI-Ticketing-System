from flask import Flask, request, Response
import json
import boto3
import re
import os
import zipfile
import inspect
import time
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

sqs_dlq_name = os.getenv("SQS_DLQ_NAME")
sqs_lp_name = os.getenv("SQS_LOW_PRIORITY_NAME")
sqs_mp_name = os.getenv("SQS_MEDIUM_PRIORITY_NAME")
sqs_hp_name = os.getenv("SQS_HIGH_PRIORITY_NAME")

lambda_lp_name = os.getenv("LAMBDA_LOW_PRIORITY_NAME")
lambda_mp_name = os.getenv("LAMBDA_MEDIUM_PRIORITY_NAME")
lambda_hp_name = os.getenv("LAMBDA_HIGH_PRIORITY_NAME")

s3_bucket_name = os.getenv("S3_BUCKET_NAME")

lp_iam_policy_name = os.getenv("LOW_PRIORITY_IAM_POLICY_NAME")
lp_iam_role_name = os.getenv("LOW_PRIORITY_IAM_ROLE_NAME")
mp_iam_policy_name = os.getenv("MEDIUM_PRIORITY_IAM_POLICY_NAME")
mp_iam_role_name = os.getenv("MEDIUM_PRIORITY_IAM_ROLE_NAME")
hp_iam_policy_name = os.getenv("HIGH_PRIORITY_IAM_POLICY_NAME")
hp_iam_role_name = os.getenv("HIGH_PRIORITY_IAM_ROLE_NAME")

trello_api_key = os.getenv("TRELLO_API_KEY")
trello_api_token = os.getenv("TRELLO_API_TOKEN")
trello_board_ID = os.getenv("TRELLO_BOARD_ID")
trello_list_name = os.getenv("TRELLO_LIST_NAME")

slack_url = os.getenv("SLACK_URL")

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
        dict = {"Title": title, "Description": description}
        match priority:
            case "low":
                dict["Priority"] = "Low"
                sendToQueue(dict, sqs_lp_name)
            case "medium":
                dict["Priority"] = "Medium"
                sendToQueue(dict, sqs_mp_name)
            case "high":
                dict["Priority"] = "High"
                sendToQueue(dict, sqs_hp_name)
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
    url = sqs.get_queue_url(QueueName=sqsName)["QueueUrl"]
    
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
        dql_url = sqs.get_queue_url(QueueName=sqs_dlq_name)["QueueUrl"]
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
            sqs.get_queue_url(QueueName=sqs_lp_name)
        except:
            sqs.create_queue(QueueName=sqs_lp_name, Attributes=attributes)
        
        try:
            sqs.get_queue_url(QueueName=sqs_mp_name)
        except:
            sqs.create_queue(QueueName=sqs_mp_name, Attributes=attributes)

        try:
            sqs.get_queue_url(QueueName=sqs_hp_name)
        except:
            sqs.create_queue(QueueName=sqs_hp_name, Attributes=attributes)
    except Exception as e:
        shutdown(e)

def initialiseS3():
    s3 = boto3.client("s3")
    try:
        s3.create_bucket(Bucket=s3_bucket_name, CreateBucketConfiguration={'LocationConstraint': aws_region})
    except Exception as e:
        if "BucketAlreadyOwnedByYou" not in str(e):
            shutdown(e)

def initialiseIAM():
    iam = boto3.client("iam")
    queues = [sqs_lp_name, sqs_mp_name, sqs_hp_name]
    policies = [lp_iam_policy_name, mp_iam_policy_name, hp_iam_policy_name]
    roles = [lp_iam_role_name, mp_iam_role_name, hp_iam_role_name]

    for queue, policy, role in zip(queues, policies, roles):
        try:
            aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
            try:
                policy_arn = f'arn:aws:iam::{aws_account_id}:policy/{policy}'
                iam.get_policy(PolicyArn=policy_arn)
            except:
                iam.create_policy(
                    PolicyName=policy,
                    PolicyDocument=json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "sqs:ReceiveMessage",
                                    "sqs:DeleteMessage",
                                    "sqs:GetQueueAttributes",
                                    "sqs:GetQueueUrl",
                                    "sqs:ListQueues",
                                    "sqs:SendMessage"
                                ],
                                "Resource": [
                                    f"arn:aws:sqs:{aws_region}:{aws_account_id}:{queue}",
                                ]
                            }
                        ]
                    })
                )
            if policy == lp_iam_policy_name:
                s3_policy_arn = f'arn:aws:iam::{aws_account_id}:policy/{lp_iam_policy_name}-s3'
                try:
                    iam.get_policy(PolicyArn=s3_policy_arn)
                except:
                    iam.create_policy(
                        PolicyName=f'{lp_iam_policy_name}-s3',
                        PolicyDocument=json.dumps({
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "s3:PutObject",
                                    ],
                                    "Resource": f"arn:aws:s3:::{s3_bucket_name}/*"
                                }
                            ]
                        })
                    )
        except Exception as e:
            shutdown(e)
        
        try:
            try:
                iam.get_role(RoleName=role)
            except:
                iam.create_role(
                    RoleName=role,
                    AssumeRolePolicyDocument=json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "lambda.amazonaws.com"
                                },
                                "Action": "sts:AssumeRole"
                            }
                        ]
                    })
                )
                iam.attach_role_policy(
                    RoleName=role,
                    PolicyArn=f'arn:aws:iam::{aws_account_id}:policy/{policy}'
                )
                if policy == lp_iam_policy_name:
                    iam.attach_role_policy(
                        RoleName=role,
                        PolicyArn=f'arn:aws:iam::{aws_account_id}:policy/{lp_iam_policy_name}-s3'
                    )
        except Exception as e:
            shutdown(e)

def initialiseLambda(trello_list_id):
    lambda_client = boto3.client("lambda")
    aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
    lambdas = [lambda_lp_name, lambda_mp_name, lambda_hp_name]
    functions = [lp_lambda, mp_lambda, hp_lambda]
    roles = [lp_iam_role_name, mp_iam_role_name, hp_iam_role_name]
    queues = [sqs_lp_name, sqs_mp_name, sqs_hp_name]

    for lambda_name, function, role, queue in zip(lambdas, functions, roles, queues):
        try:
            try:
                lambda_client.get_function(FunctionName=lambda_name)
            except:
                function_name = function.__name__
                function_string = inspect.getsource(function)
                function_string = function_string.replace(f"{function_name}", "lambda_handler")
                match function_name:
                    case "lp_lambda":
                        function_string = function_string.replace("<bucket_name>", s3_bucket_name)
                        function_string = function_string.replace("<region_name>", aws_region)
                    case "mp_lambda":
                        function_string = function_string.replace("<trello_api_key>", trello_api_key)
                        function_string = function_string.replace("<trello_api_token>", trello_api_token)
                        function_string = function_string.replace("<trello_list_id>", trello_list_id)
                    case "hp_lambda":
                        function_string = function_string.replace("<slack_url>", slack_url)

                with open(f"./{function_name}.py", "w") as f:
                    f.write(function_string)

                if os.path.exists("./lambda_function.zip"):
                    os.remove("./lambda_function.zip")

                with zipfile.ZipFile("./lambda_function.zip", "w") as z:
                    z.write(f"./{function_name}.py", arcname="lambda_function.py")

                for _ in range(10):
                    try:
                        with open("./lambda_function.zip", "rb") as f:
                            lambda_client.create_function(
                                FunctionName=lambda_name,
                                Runtime='python3.8',
                                Role=f'arn:aws:iam::{aws_account_id}:role/{role}',
                                Handler='lambda_function.lambda_handler',
                                Code={'ZipFile': f.read()},
                                Timeout=30,
                                MemorySize=128,
                                Publish=True
                            )
                            lambda_client.create_event_source_mapping(
                                EventSourceArn=f'arn:aws:sqs:{aws_region}:{aws_account_id}:{queue}',
                                FunctionName=lambda_name,
                                Enabled=True,
                                BatchSize=10
                            )
                        break
                    except Exception as e:
                        if "The role defined for the function cannot be assumed by Lambda" not in str(e):
                            break
                        print("Waiting for IAM role to be ready")
                        time.sleep(2)

                os.remove("./lambda_function.zip")
                os.remove(f"./{function_name}.py")
        except Exception as e:
            return shutdown(e)

def lp_lambda(event, context):
    import boto3
    import json
    import time

    try:
        sqs_msg = json.loads(event['Records'][0]['body'])
        del sqs_msg["Priority"]

        s3Client = boto3.client("s3", region_name="<region_name>")
        bucket_name = "<bucket_name>"

        title = sqs_msg.get("Title", "Untitled").replace(" ", "_")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        unique_filename = f"{timestamp}_{title}_Ticket.json"

        response = s3Client.put_object(Bucket=bucket_name, Key=unique_filename, Body=json.dumps(sqs_msg))

        return {
            "status" : 200,
            "body" : "S3 upload success"
        }
    except Exception as e:
        print("Client connection to S3 failed because ", e)
        return{
            "status" : 500,
            "body" : "S3 upload failed"
        }

def mp_lambda(event, context):
    import json
    import urllib3

    try:
        sqs_msg = json.loads(event['Records'][0]['body'])
        http = urllib3.PoolManager()

        url = f"https://api.trello.com/1/cards"
        title = sqs_msg.get("Title", "Untitled")
        description = sqs_msg.get("Description", "No description provided")

        query = {
            "idList": "<trello_list_id>",
            "key": "<trello_api_key>",
            "token": "<trello_api_token>",
            "name": title,
            "desc": description
        }

        r = http.request("POST", url, body=json.dumps(query), headers={"Content-Type": "application/json"})

        return {
            "status" : 200,
            "body" : "Trello upload success"
        }
    except Exception as e:
        print("Client connection to Trello failed because ", e)
        return{
            "status" : 500,
            "body" : "Trello upload failed"
        }

def hp_lambda(event, context):
    import json
    import urllib3

    try:
        sqs_msg = json.loads(event['Records'][0]['body'])
        http = urllib3.PoolManager()
        
        message = f"Title: {sqs_msg['Title']}\nDescription: {sqs_msg['Description']}"
        data = {"text": message}
        
        r = http.request("POST",
                        "https://hooks.slack.com/services/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",
                        body = json.dumps(data),
                        headers = {"Content-Type": "application/json"})

        return {
            "status" : 200,
            "body" : "Slack upload success"
        }
    except Exception as e:
        print("Client connection to Slack failed because ", e)
        return{
            "status" : 500,
            "body" : "Slack upload failed"
        }

def shutdown(reason=""):
    if reason:
        print(reason)
    else:
        print("Error initializing resources")
    print("Shutting down")
    exit()
    
def get_trello_list():
    url = f"https://api.trello.com/1/boards/{trello_board_ID}/lists"

    headers = {
        "Accept": "application/json"
    }

    query = {
        'key': trello_api_key,
        'token': trello_api_token
    }

    response = requests.request("GET", url, headers=headers, params=query)
    lists = json.loads(response.text)

    list_id = ""
    for list in lists:
        if list["name"].lower() == trello_list_name.lower():
            list_id = list["id"]
            return list_id
    if list_id == "":
        return shutdown("List not found") 


@app.route("/health", methods=["GET"])
def health():
    return Response("Healthy", status=200)

initialised = False
@app.route("/initialise", methods=["POST"])
def initialise():
    global initialised
    if initialised:
        return Response("Already initialised", status=200)
    print("Initialising resources")

    boto3.setup_default_session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=aws_region)
    trello_list_id = get_trello_list()
    
    initializeSQS()
    initialiseS3()
    initialiseIAM()
    initialiseLambda(trello_list_id)
    
    print("Initialisation complete")
    initialised = True
    return Response("Initialised", status=200)


if __name__ == "__main__":
    app.run()
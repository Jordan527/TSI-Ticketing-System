from flask import Flask, request, Response
import json
import boto3
import re
import os
import zipfile
import inspect
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

iam_policy_name = os.getenv("IAM_POLICY_NAME")
iam_role_name = os.getenv("IAM_ROLE_NAME")

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
                sendToQueue(dict, sqs_low_priority_name)
            case "medium":
                sendToQueue(dict, sqs_medium_priority_name)
            case "high":
                sendToQueue(dict, sqs_high_priority_name)
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
            sqs.get_queue_url(QueueName=sqs_low_priority_name)
        except:
            sqs.create_queue(QueueName=sqs_low_priority_name, Attributes=attributes)
        
        try:
            sqs.get_queue_url(QueueName=sqs_medium_priority_name)
        except:
            sqs.create_queue(QueueName=sqs_medium_priority_name, Attributes=attributes)

        try:
            sqs.get_queue_url(QueueName=sqs_high_priority_name)
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

def initialiseIAM():
    iam = boto3.client("iam")
    try:
        aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
        try:
            policy_arn = f'arn:aws:iam::{aws_account_id}:policy/{iam_policy_name}'
            iam.get_policy(PolicyArn=policy_arn)
        except:
            iam.create_policy(
                PolicyName=iam_policy_name,
                PolicyDocument=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:PutObject",
                            ],
                            "Resource": f"arn:aws:s3:::{s3_bucket_name}/*"
                        },
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
                                f"arn:aws:sqs:{aws_region}:{aws_account_id}:{sqs_low_priority_name}",
                            ]
                        }
                    ]
                })
            )
        
        try:
            iam.get_role(RoleName=iam_role_name)
        except:
            iam.create_role(
                RoleName=iam_role_name,
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
                RoleName=iam_role_name,
                PolicyArn=policy_arn
            )
    except Exception as e:
        shutdown(e)

def initialiseLowPriorityLambda():
    try:
        lambda_client = boto3.client("lambda")
        aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
        try:
            lambda_client.get_function(FunctionName=lambda_low_priority_name)
        except:
            function_string = inspect.getsource(low_priority_lambda)
            function_string = function_string.replace("low_priority_lambda", "lambda_handler")
            function_string = function_string.replace("<bucket_name>", s3_bucket_name)
            function_string = function_string.replace("<region_name>", aws_region)

            
            with open("./low_priority_lambda.py", "w") as f:
                f.write(function_string)

            if os.path.exists("./lambda_function.zip"):
                os.remove("./lambda_function.zip")

            with zipfile.ZipFile("./low_priority_lambda.zip", "w") as z:
                z.write("./low_priority_lambda.py", arcname="lambda_function.py")

            import time
            for _ in range(10):
                try:
                    with open("./low_priority_lambda.zip", "rb") as f:
                        lambda_client.create_function(
                            FunctionName=lambda_low_priority_name,
                            Runtime='python3.8',
                            Role=f'arn:aws:iam::{aws_account_id}:role/{iam_role_name}',
                            Handler='lambda_function.lambda_handler',
                            Code={'ZipFile': f.read()},
                            Timeout=30,
                            MemorySize=128,
                            Publish=True
                        )
                        lambda_client.create_event_source_mapping(
                            EventSourceArn=f'arn:aws:sqs:{aws_region}:{aws_account_id}:{sqs_low_priority_name}',
                            FunctionName=lambda_low_priority_name,
                            Enabled=True,
                            BatchSize=10
                        )
                    break
                except Exception as e:
                    if "The role defined for the function cannot be assumed by Lambda" not in str(e):
                        break
                    print("Waiting for IAM role to be ready")
                    time.sleep(2)


            os.remove("./low_priority_lambda.zip")
            os.remove("./low_priority_lambda.py")
    except Exception as e:
        shutdown(e)

def low_priority_lambda(event, context):
    import boto3
    import json
    import uuid
    import time

    try:
        bucket_name = "<bucket_name>"
        sqs_msg = json.loads(event['Records'][0]['body'])
        s3Client = boto3.client("s3", region_name="<region_name>")
        title = sqs_msg.get("Title", "Untitled").replace(" ", "_")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        unique_filename = f"Ticket_{title}_{timestamp}.json"
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
    initialiseIAM()
    initialiseLowPriorityLambda()

if __name__ == "__main__":
    app.run()
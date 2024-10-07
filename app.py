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

prefix = ""
sqs_dlq = ""
sqs_lp = ""
sqs_mp = ""
sqs_hp = ""

lp_lambda = ""
mp_lambda = ""
hp_lambda = ""

s3_bucket = ""

lp_iam_policy = ""
lp_iam_role = ""
mp_iam_policy = ""
mp_iam_role = ""
hp_iam_policy = ""
hp_iam_role = ""

trello_api_key = ""
trello_api_token = ""
trello_board_ID = ""
trello_list_name = ""

slack_url = ""

initialised = False
initialisation_error = False
exiting = False
error_reason = ""

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
        
    response = sqs.send_message( 
        QueueUrl=url, 
        DelaySeconds=10, 
        MessageBody=( 
            json_payload 
        ) 
    ) 

def initialiseLogging(logging_level=logging.INFO):
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename="app.log", level=logging_level, format="%(asctime)s - %(message)s")

def initialiseBoto3():
    global aws_region
    aws_region = str(os.environ.get("AWS_REGION"))
    aws_access_key_id = str(os.environ.get("AWS_ACCESS_KEY_ID"))
    aws_secret_access_key = str(os.environ.get("AWS_SECRET_ACCESS_KEY"))
    if aws_region and aws_access_key_id and aws_secret_access_key:
        boto3.Session()
        boto3.setup_default_session(region_name=aws_region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    else:
        log_error("AWS credentials not found", shutdown=True, initialisation=True)

def get_secrets():
    try:
        secret_client = boto3.client("secretsmanager")
        response = secret_client.list_secrets()
        secrets = response["SecretList"]
        requried_secrets = ["PREFIX", "TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_BOARD_ID", "TRELLO_LIST_NAME", "SLACK_URL"]
        for secret in secrets:
            if secret["Name"] == "ticketing-app":
                secret_value = secret_client.get_secret_value(SecretId=secret["ARN"])
                secret_string = secret_value["SecretString"]
                secret_dict = json.loads(secret_string)
                missing_secrets = []
                for key in requried_secrets:
                    if key not in secret_dict:
                        missing_secrets.append(key)
                if missing_secrets:
                    log_error(f"Missing secrets: {missing_secrets}", shutdown=True, initialisation=True)
                else:
                    global prefix, trello_api_key, trello_api_token, trello_board_ID, trello_list_name, slack_url
                    prefix = secret_dict["PREFIX"]
                    trello_api_key = secret_dict["TRELLO_API_KEY"]
                    trello_api_token = secret_dict["TRELLO_API_TOKEN"]
                    trello_board_ID = secret_dict["TRELLO_BOARD_ID"]
                    trello_list_name = secret_dict["TRELLO_LIST_NAME"]
                    slack_url = secret_dict["SLACK_URL"]
                    return
    except Exception as e:
        log_error(e, shutdown=True, initialisation=True)

def create_global_variables():
    global prefix, sqs_dlq, sqs_lp, sqs_mp, sqs_hp, lp_lambda, mp_lambda, hp_lambda, s3_bucket, lp_iam_policy, lp_iam_role, mp_iam_policy, mp_iam_role, hp_iam_policy, hp_iam_role
    sqs_dlq = f"{prefix}-DLQ"
    sqs_lp = f"{prefix}-LP"
    sqs_mp = f"{prefix}-MP"
    sqs_hp = f"{prefix}-HP"

    lp_lambda = f"{prefix}-LP"
    mp_lambda = f"{prefix}-MP"
    hp_lambda = f"{prefix}-HP"

    s3_bucket = f"{prefix}-bucket"

    lp_iam_policy = f"{prefix}-LP-Policy"
    lp_iam_role = f"{prefix}-LP-Role"
    mp_iam_policy = f"{prefix}-MP-Policy"
    mp_iam_role = f"{prefix}-MP-Role"
    hp_iam_policy = f"{prefix}-HP-Policy"
    hp_iam_role = f"{prefix}-HP-Role"

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
        log_error("Trello list not found", shutdown=True, initialisation=True) 

def initializeSQS():
    sqs = boto3.client("sqs")

    try:
        dql_url = sqs.get_queue_url(QueueName=sqs_dlq)["QueueUrl"]
    except:
        dql_url = sqs.create_queue(QueueName=sqs_dlq)["QueueUrl"]

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
            sqs.get_queue_url(QueueName=sqs_lp)
        except:
            sqs.create_queue(QueueName=sqs_lp, Attributes=attributes)
        
        try:
            sqs.get_queue_url(QueueName=sqs_mp)
        except:
            sqs.create_queue(QueueName=sqs_mp, Attributes=attributes)

        try:
            sqs.get_queue_url(QueueName=sqs_hp)
        except:
            sqs.create_queue(QueueName=sqs_hp, Attributes=attributes)
    except Exception as e:
        log_error(e, shutdown=True, initialisation=True)

def initialiseS3():
    s3 = boto3.client("s3")
    try:
        s3.create_bucket(Bucket=s3_bucket, CreateBucketConfiguration={'LocationConstraint': aws_region})
    except Exception as e:
        if "BucketAlreadyOwnedByYou" not in str(e):
            log_error(e, shutdown=True, initialisation=True)

def initialiseIAM():
    iam = boto3.client("iam")
    queues = [sqs_lp, sqs_mp, sqs_hp]
    policies = [lp_iam_policy, mp_iam_policy, hp_iam_policy]
    roles = [lp_iam_role, mp_iam_role, hp_iam_role]

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
            if policy == lp_iam_policy:
                s3_policy_arn = f'arn:aws:iam::{aws_account_id}:policy/{lp_iam_policy}-s3'
                try:
                    iam.get_policy(PolicyArn=s3_policy_arn)
                except:
                    iam.create_policy(
                        PolicyName=f'{lp_iam_policy}-s3',
                        PolicyDocument=json.dumps({
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "s3:PutObject",
                                    ],
                                    "Resource": f"arn:aws:s3:::{s3_bucket}/*"
                                }
                            ]
                        })
                    )
        except Exception as e:
            log_error(e, shutdown=True, initialisation=True)
        
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
                if policy == lp_iam_policy:
                    iam.attach_role_policy(
                        RoleName=role,
                        PolicyArn=f'arn:aws:iam::{aws_account_id}:policy/{lp_iam_policy}-s3'
                    )
        except Exception as e:
            log_error(e, shutdown=True, initialisation=True)

def initialiseLambda(trello_list_id):
    lambda_client = boto3.client("lambda")
    aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
    lambdas = [lp_lambda, mp_lambda, hp_lambda]
    functions = [lp_lambda_function, mp_lambda_function, hp_lambda_function]
    roles = [lp_iam_role, mp_iam_role, hp_iam_role]
    queues = [sqs_lp, sqs_mp, sqs_hp]

    for lambda_name, function, role, queue in zip(lambdas, functions, roles, queues):
        try:
            try:
                lambda_client.get_function(FunctionName=lambda_name)
            except:
                function_name = function.__name__
                function_string = inspect.getsource(function)
                function_string = function_string.replace(f"{function_name}", "lambda_handler")
                match function_name:
                    case "lp_lambda_function":
                        function_string = function_string.replace("<bucket_name>", s3_bucket)
                        function_string = function_string.replace("<region_name>", aws_region)
                    case "mp_lambda_function":
                        function_string = function_string.replace("<trello_api_key>", trello_api_key)
                        function_string = function_string.replace("<trello_api_token>", trello_api_token)
                        function_string = function_string.replace("<trello_list_id>", trello_list_id)
                    case "hp_lambda_function":
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
            return log_error(e, shutdown=True, initialisation=True)

def lp_lambda_function(event, context):
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

def mp_lambda_function(event, context):
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

def hp_lambda_function(event, context):
    import json
    import urllib3

    try:
        sqs_msg = json.loads(event['Records'][0]['body'])
        http = urllib3.PoolManager()
        
        message = f"Title: {sqs_msg['Title']}\nDescription: {sqs_msg['Description']}"
        data = {"text": message}
        
        r = http.request("POST",
                        "<slack_url>",
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

    # variables = get_variables()
    # logging.info(variables)
    
def get_variables():
    output = ""
    output += "Boto3 session:\n"
    output += f"Region: {boto3.session.Session().region_name}\n"
    output += f"Access key: {boto3.Session().get_credentials().access_key}\n"
    output += f"Secret key: {boto3.Session().get_credentials().secret_key}\n"
    output += "\nGlobal variables:\n"
    output += f"prefix: {prefix}\n"
    output += f"sqs_dlq: {sqs_dlq}\n"
    output += f"sqs_lp: {sqs_lp}\n"
    output += f"sqs_mp: {sqs_mp}\n"
    output += f"sqs_hp: {sqs_hp}\n"
    output += f"lp_lambda: {lp_lambda}\n"
    output += f"mp_lambda: {mp_lambda}\n"
    output += f"hp_lambda: {hp_lambda}\n"
    output += f"s3_bucket: {s3_bucket}\n"
    output += f"lp_iam_policy: {lp_iam_policy}\n"
    output += f"lp_iam_role: {lp_iam_role}\n"
    output += f"mp_iam_policy: {mp_iam_policy}\n"
    output += f"mp_iam_role: {mp_iam_role}\n"
    output += f"hp_iam_policy: {hp_iam_policy}\n"
    output += f"hp_iam_role: {hp_iam_role}\n"
    output += f"trello_api_key: {trello_api_key}\n"
    output += f"trello_api_token: {trello_api_token}\n"
    output += f"trello_board_ID: {trello_board_ID}\n"
    output += f"trello_list_name: {trello_list_name}\n"
    output += f"slack_url: {slack_url}\n"
    return output

@app.route("/health", methods=["GET"])
def health():
    return Response("Healthy", status=200)

@app.route("/initialise", methods=["POST"])
def initialise():
    global initialised, initialisation_error
    if initialised:
        return Response("Already initialised", status=200)
    initialisation_error = False
    print("Initialising resources")

    initialiseLogging()

    initialiseBoto3()
    if initialisation_error:
        return Response(error_reason, status=500)
    get_secrets()
    if initialisation_error:
        return Response(error_reason, status=500)
    create_global_variables()
    if initialisation_error:
        return Response(error_reason, status=500)
    trello_list_id = get_trello_list()
    
    if initialisation_error:
        return Response(error_reason, status=500)
    initializeSQS()
    if initialisation_error:
        return Response(error_reason, status=500)
    initialiseS3()
    if initialisation_error:
        return Response(error_reason, status=500)
    initialiseIAM()
    if initialisation_error:
        return Response(error_reason, status=500)
    initialiseLambda(trello_list_id)
    if initialisation_error:
        return Response(error_reason, status=500)

    print("Initialisation complete")
    initialised = True
    return Response("Initialised", status=200)

@app.after_request
def exit(response):
    global exiting
    if exiting:
        logging.error("Exiting")
        os._exit(1)
    return response

if __name__ == "__main__":
    app.run()
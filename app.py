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

@app.route("/initialise", methods=["POST"])
def initialise():
    reset_error()
    print("Initialising resources")

    initialiseLogging()

    state = get_state()
    if initialisation_error:
        return Response(error_reason, status=500)

    initialiseBoto3()
    if initialisation_error:
        return Response(error_reason, status=500)
    
    get_secrets()
    if initialisation_error:
        return Response(error_reason, status=500)
    
    differences = check_state(state)
    if initialisation_error:
        return Response(error_reason, status=500)

    if state:
        if differences:
            if "prefix" in differences or "aws_region" in differences:
                create_global_variables(state["prefix"])
                if "aws_region" in differences:
                    initialiseBoto3(state["aws_region"])

                try:
                    delete_lambda([lp_lambda, mp_lambda, hp_lambda])
                    delete_all_iam_roles()
                    delete_all_iam_policies()
                    delete_s3_bucket()
                    delete_all_queues()
                except Exception as e:
                    log_error(e, shutdown=True, initialisation=True)
                    return Response(error_reason, status=500)
                
            elif "trello_api_key" in differences or "trello_api_token" in differences or "trello_board_ID" in differences or "trello_list_name" in differences:
                try:
                    create_global_variables()
                    delete_lambda([mp_lambda])
                except Exception as e:
                    log_error(e, shutdown=True, initialisation=True)
                    return Response(error_reason, status=500)
                
            elif "slack_url" in differences:
                try:
                    create_global_variables()
                    delete_lambda([hp_lambda])
                except Exception as e:
                    log_error(e, shutdown=True, initialisation=True)
                    return Response(error_reason, status=500)
            
            initialiseBoto3()
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
        if "conflicting conditional operation" in error_reason:
            reset_error()
            initialiseBoto3(state["aws_region"])
            initialiseS3()
            if initialisation_error:
                return Response(error_reason, status=500)
            initialiseBoto3()
        else:
            return Response(error_reason, status=500)
    
    initialiseIAMPolicies()
    if initialisation_error:
        return Response(error_reason, status=500)
    
    initialiseIAMRoles()
    if initialisation_error:
        return Response(error_reason, status=500)
    
    initialiseLambda(trello_list_id)
    if initialisation_error:
        return Response(error_reason, status=500)

    save_state(state, differences)

    print("Initialisation complete")
    return Response("Initialised", status=200)

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

# Define the functions to get and save the state
def get_state():
    try:
        if os.path.exists("state.json"):
            with open("state.json", "r") as f:
                state = json.load(f)
        else:
            with open("state.json", "w") as f:
                json.dump({}, f)
            state = {}
        return state
    except Exception as e:
        log_error(e, shutdown=True, initialisation=True)
        return {}
    
def check_state(state):
    variables = {
        "aws_region": aws_region,
        "prefix": prefix,
        "trello_api_key": trello_api_key,
        "trello_api_token": trello_api_token,
        "trello_board_ID": trello_board_ID,
        "trello_list_name": trello_list_name,
        "slack_url": slack_url
    }
    try:
        differences = []
        for key in variables:
            if key not in state or state[key] != variables[key]:
                differences.append(key)
        return differences
    except Exception as e:
        log_error(e, shutdown=True, initialisation=True)
        return []

def save_state(state, differences):
    try:
        if differences:
            for key in differences:
                state[key] = globals()[key]
            with open("state.json", "w") as f:
                json.dump(state, f)
    except Exception as e:
        log_error(e, shutdown=True, initialisation=True)

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
    logging.basicConfig(filename="app.log", level=logging_level, format="%(asctime)s - %(message)s")

def initialiseBoto3(old_region=None):
    global aws_region
    if old_region:
        aws_region = old_region
    else:
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
        secret_client = boto3.client("secretsmanager", region_name=aws_region)
        response = secret_client.list_secrets()
        secrets = response["SecretList"]
        if not secrets:
            return log_error("No secrets found", shutdown=True, initialisation=True)
        
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

def create_global_variables(old_prefix=None):
    if not old_prefix:
        global prefix, sqs_dlq, sqs_lp, sqs_mp, sqs_hp, lp_lambda, mp_lambda, hp_lambda, s3_bucket, lp_iam_policy, lp_iam_role, mp_iam_policy, mp_iam_role, hp_iam_policy, hp_iam_role
    else:
        global sqs_dlq, sqs_lp, sqs_mp, sqs_hp, lp_lambda, mp_lambda, hp_lambda, s3_bucket, lp_iam_policy, lp_iam_role, mp_iam_policy, mp_iam_role, hp_iam_policy, hp_iam_role
        prefix = old_prefix

    
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
        try:
            dql_url = sqs.get_queue_url(QueueName=sqs_dlq)["QueueUrl"]
        except:
            dql_url = sqs.create_queue(QueueName=sqs_dlq)["QueueUrl"]

        dlq_attributes = sqs.get_queue_attributes(QueueUrl=dql_url, AttributeNames=['QueueArn'])
        dlq_arn = dlq_attributes['Attributes']['QueueArn']

        redrive_policy = {
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': '3'
        }

        attributes = {
            'RedrivePolicy': json.dumps(redrive_policy)
        }

        queues = [sqs_lp, sqs_mp, sqs_hp]
        for queue in queues:
            try:
                sqs.get_queue_url(QueueName=queue)
            except:
                try:
                    sqs.create_queue(QueueName=queue, Attributes=attributes)
                except Exception as e:
                    return log_error(e, shutdown=True, initialisation=True)
                        
    except Exception as e:
        if "QueueDeletedRecently" not in str(e):
            log_error(e, shutdown=True, initialisation=True)
        else:
            log_error(e)
            time.sleep(10)
            initializeSQS()

def initialiseS3():
    s3 = boto3.client("s3")
    try:
        s3.create_bucket(Bucket=s3_bucket, CreateBucketConfiguration={'LocationConstraint': aws_region})
    except Exception as e:
        if "BucketAlreadyOwnedByYou" not in str(e):
            log_error(e, shutdown=True, initialisation=True)

def initialiseIAMPolicies():
    aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
    iam = boto3.client("iam")
    queues = [sqs_lp, sqs_mp, sqs_hp]
    policies = [lp_iam_policy, mp_iam_policy, hp_iam_policy]

    for queue, policy in zip(queues, policies):
        try:
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

def initialiseIAMRoles():
    aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
    iam = boto3.client("iam")
    policies = [lp_iam_policy, mp_iam_policy, hp_iam_policy]
    roles = [lp_iam_role, mp_iam_role, hp_iam_role]

    for policy, role in zip(policies, roles):      
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

# Define the functions to delete the resources
def delete_lambda(lambdas):
    lambda_client = boto3.client("lambda")
    print("Lambdas: ", lambdas)
    for lambda_name in lambdas:
        try:
            lambda_client.delete_function(FunctionName=lambda_name)
        except lambda_client.exceptions.ResourceNotFoundException:
            pass

def detach_all_policies(role):
    iam = boto3.client("iam")
    response = iam.list_attached_role_policies(RoleName=role)
    policies = response["AttachedPolicies"]
    for policy in policies:
        try:
            iam.detach_role_policy(RoleName=role, PolicyArn=policy["PolicyArn"])
        except iam.exceptions.NoSuchEntityException:
            pass

def delete_all_iam_roles():
    iam = boto3.client("iam")
    roles = [lp_iam_role, mp_iam_role, hp_iam_role]
    for role in roles:
        try:
            detach_all_policies(role)
            iam.delete_role(RoleName=role)
        except iam.exceptions.NoSuchEntityException:
            pass

def delete_all_iam_policies():
    iam = boto3.client("iam")
    policies = [lp_iam_policy, lp_iam_policy + "-s3", mp_iam_policy, hp_iam_policy]
    for policy in policies:
        try:
            aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
            iam.delete_policy(PolicyArn=f'arn:aws:iam::{aws_account_id}:policy/{policy}')
        except iam.exceptions.NoSuchEntityException:
            pass    

def delete_s3_bucket():
    s3 = boto3.client("s3")
    try:
        objects = s3.list_objects(Bucket=s3_bucket)
        if "Contents" in objects:
            for obj in objects["Contents"]:
                s3.delete_object(Bucket=s3_bucket, Key=obj["Key"])
        s3.delete_bucket(Bucket=s3_bucket)
        print("Deleted S3 bucket")
    except s3.exceptions.NoSuchBucket:
        pass

def delete_all_queues():
    sqs = boto3.client("sqs")
    queues = [sqs_dlq, sqs_lp, sqs_mp, sqs_hp]
    for queue in queues:
        try:
            sqs.delete_queue(QueueUrl=sqs.get_queue_url(QueueName=queue)["QueueUrl"])
            print("Deleted queue: ", queue)
        except sqs.exceptions.QueueDoesNotExist:
            pass


if __name__ == "__main__":
    app.run()
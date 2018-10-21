from __future__ import print_function

import boto3
import json
import os

print('Loading function')
dynamo = boto3.client('dynamodb')

debug = os.getenv('DEBUG', 'false')
taco_name = os.getenv('EMOJI', 'taco')
verification_token = os.environ['SLACK_VERIF_TOKEN']
msg_processor_arn = os.environ['MSG_PROC_ARN']

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }



def slack_url_verification(body):
    return respond(None, {
        'challenge': body['challenge']
    })


def enqueue_body(body):
    client = boto3.client('sns')

    client.publish(
        TargetArn=msg_processor_arn,
        Message=body
    )

# main
def lambda_handler(event, context):
    # Get POST body
    try:
        body = json.loads(event['body'])
    except ValueError as e:
        return respond(e)

    # Check Token
    if body['token'] != verification_token:
        return respond(Exception('Invalid Token'))

    # Route Body
    if debug == 'true':
        print("Got body: " + json.dumps(body, indent=2))

    if body['type'] == 'url_verification':
        return slack_url_verification(body)
    elif body['type'] == 'event_callback' and body['event']['type'] == 'message':
        enqueue_body(event['body'])
        return respond(None, {
            'status': 'ok'
        })
    else:
        return respond(None, {
            'status': 'ok'
        })

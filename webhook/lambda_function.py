from __future__ import print_function

import boto3
import json
import os
import re

print('Loading function')
dynamo = boto3.client('dynamodb')


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def find_taco(message):
    taco_name = os.getenv('EMOJI', 'taco')
    taco_re = r':' + re.escape(taco_name) + r':'
    values = re.findall(taco_re, message)
    return len(values)


def slack_message(body):
    taco_count = find_taco(body['event']['text'])
    if taco_count > 0:
        if os.getenv('DEBUG', 'false') == 'true': print("Found "+ str(taco_count) + " taco(s)")

    return respond(None, {
        'status': 'ok'
    })


def slack_url_verification(body):
    return respond(None, {
        'challenge': body['challenge']
    })


def lambda_handler(event, context):
    # Get POST body
    try:
        body = json.loads(event['body'])
    except ValueError as e:
        return respond(e)

    # Check Token
    if body['token'] != os.environ['SLACK_VERIF_TOKEN']:
        return respond(Exception('Invalid Token'))

    # Route Body
    if os.getenv('DEBUG', 'false') == 'true':
        print("Got body: " + json.dumps(body, indent=2))

    if body['type'] == 'url_verification':
        return slack_url_verification(body)
    elif body['type'] == 'event_callback' and body['event']['type'] == 'message':
        return slack_message(body)
    else:
        return respond(None, event)

from __future__ import print_function

import boto3
import json
import os

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
    print("Got body: " + json.dumps(body, indent=2))

    if body['type'] == 'url_verification':
        return slack_url_verification(body)
    else:
        return respond(None, event)

from __future__ import print_function

import boto3
import datetime
import json
import os
import re

print('Loading function')
dynamo = boto3.client('dynamodb')

debug = os.getenv('DEBUG', 'false')
taco_name = os.getenv('EMOJI', 'taco')
timezone = os.getenv('TZ_OFFSET', 0)
verification_token = os.environ['SLACK_VERIF_TOKEN']


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def find_taco(message):
    taco_re = r':' + re.escape(taco_name) + r':'
    values = re.findall(taco_re, message)
    return len(values)


def find_users(message, myself):
    values = re.findall(r'<@(U[a-zA-Z0-9]+)>', message)
    users = list(set(values))

    # Don't allow user to taco themselves
    try:
        myself_index = users.index(myself)
        if debug == 'true': print('User tried to taco themself')
        users.pop(myself_index)
    except:
        pass

    return users


def slack_message(body):
    # Find taco in channel messages
    if body['event']['channel_type'] == 'channel':
        taco_count = find_taco(body['event']['text'])
        if taco_count > 0:
            if debug == 'true': print("Found " + str(taco_count) + " taco(s)")
            taco_users = find_users(body['event']['text'], body['event']['user'])

            print("i should check to see if you have " + str(taco_count * len(taco_users)) + " tacos")

    return respond(None, {
        'status': 'ok'
    })


def slack_url_verification(body):
    return respond(None, {
        'challenge': body['challenge']
    })


def lambda_handler(event, context):
    st = datetime.datetime.now() + datetime.timedelta(hours=int(timezone))
    print(st.strftime('%Y-%m-%d %H:%M:%S'))

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
        return slack_message(body)
    else:
        return respond(None, event)

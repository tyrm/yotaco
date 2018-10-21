from __future__ import print_function

import boto3
from boto3.dynamodb.conditions import Key, Attr
import datetime
import decimal
import inflect
import json
import os
import re
import requests

print('Loading function')
dynamo = boto3.client('dynamodb')

debug = os.getenv('DEBUG', 'false')
taco_name = os.getenv('EMOJI', 'taco')
timezone = os.getenv('TZ_OFFSET', 0)
verification_token = os.environ['SLACK_VERIF_TOKEN']
bot_token = os.environ['SLACK_BOT_TOKEN']


def dynamo_add_taco(ts, index, team, channel, fromu, tou):
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('taco_transactions')

    response = table.put_item(
        Item={
            'tid': str(ts) + "-" + team + "-" + channel + "-" + str(index),
            'timestamp': decimal.Decimal(ts),
            'channel': channel,
            'team': team,
            'from': fromu,
            'to': tou
        }
    )

    print(json.dumps(response, indent=4))

    return


def dynamo_get_tacos_avail(user):
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('taco_transactions')

    response = table.scan(
        Select='ALL_ATTRIBUTES',
        FilterExpression=Key('from').eq(user) & Key('timestamp').gte(get_epoch(get_local_midnight()))
    )

    return 5 - response['Count']


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


def get_epoch(ts):
    return int(((ts - datetime.datetime(1970, 1, 1)) - datetime.timedelta(hours=int(timezone))).total_seconds())


def get_local_midnight():
    st = datetime.datetime.now() + datetime.timedelta(hours=int(timezone))
    midnight = datetime.datetime(st.year, st.month, st.day, 0, 0, 0)
    return midnight


def process_tacos(tc, tu, tr, body):
    index = 1
    for user in tu:
        for x in range(tc):
            dynamo_add_taco(body['event']['event_ts'], index, body['team_id'], body['event']['channel'],
                            body['event']['user'], user)
            index = index + 1

        send_message_you_got_taco(user, tc, body['event']['user'], body['event']['channel'], body['event']['text'])

    send_message_you_sent_taco(body['event']['user'], tc, tu, tr - (index - 1))
    return


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def send_message_you_got_taco(user, tc, fromu, channel, message):
    p = inflect.engine()
    text = "You received *" + str(tc) + " " + p.plural(taco_name, tc) + "* from <@" + fromu + "> in <#" + channel + ">"
    attachment = "[{\"text\": \"" + message + "\"}]"

    send_slack_message(text, user, attachment)


def send_message_you_sent_taco(user, tc, tu, tr):
    p = inflect.engine()
    text = ""
    for tuser in tu:
        text = text + "<@" + tuser + "> "
    text = text + "received *" + str(tc) + " " + p.plural(taco_name, tc) + "* from you. You have *" + \
           str(tr) + " " + p.plural(taco_name, tr) + "* left to give out today."

    send_slack_message(text, user)


def send_slack_message(message, channel, attachment=None):
    params = {"token": bot_token, "text": message, "channel": channel, "as_user": True}
    if attachment != None:
        params['attachments'] = attachment

    r = requests.get('https://slack.com/api/chat.postMessage', params=params)


def slack_message(body):
    # Find taco in channel messages
    if body['event']['channel_type'] == 'channel':
        taco_count = find_taco(body['event']['text'])
        if taco_count > 0:
            if debug == 'true': print("Found " + str(taco_count) + " taco(s)")
            taco_users = find_users(body['event']['text'], body['event']['user'])
            if len(taco_users) > 0:
                my_tacos_avail = dynamo_get_tacos_avail(body['event']['user'])
                if debug == 'true': print("you have " + str(my_tacos_avail) + " taco(s)")

                if my_tacos_avail >= (taco_count * len(taco_users)):
                    if debug == 'true': print("you can give these tacos")
                    process_tacos(taco_count, taco_users, my_tacos_avail, body)

    return respond(None, {
        'status': 'ok'
    })


def slack_url_verification(body):
    return respond(None, {
        'challenge': body['challenge']
    })


# main
def lambda_handler(event, context):
    midnight = get_local_midnight()
    print(midnight.strftime('%Y-%m-%d %H:%M:%S'))
    print(get_epoch(midnight))

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

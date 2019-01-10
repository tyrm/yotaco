from __future__ import print_function

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import datetime
import decimal
import inflect
import json
import os
import re
import requests


debug = os.getenv('DEBUG', 'false')
taco_name = os.getenv('EMOJI', 'taco')
timezone = os.getenv('TZ_OFFSET', 0)
bot_token = os.environ['SLACK_BOT_TOKEN']
bot_user  = os.environ['SLACK_BOT_USER']

print('Loading function', debug, taco_name, timezone, bot_user)

def dynamo_add_taco(ts, index, team, channel, channel_display_name, fromu, from_display_name, tou, to_display_name, message):
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')

    # Add Taco Transaction
    transaction_table = dynamodb.Table('taco_transactions')
    ts_str = "%017.6f" % float(ts)
    transaction_table.put_item(
        Item={
            'tid': ts_str + "-" + team + "-" + channel + "-" + str(index),
            'timestamp': decimal.Decimal(ts),
            'cid': get_cid_today(team),
            'channel': channel,
            'channel_display_name': channel_display_name,
            'team': team,
            'from': fromu,
            'to': tou,
            'from_display_name': from_display_name,
            'to_display_name': to_display_name,
            'message': message
        }
    )

    # Update Taco Counts
    count_ids = [
        get_cid_this_month(team),
        get_cid_this_week(team),
        get_cid_this_year(team),
        get_cid_today(team)
    ]

    count_table = dynamodb.Table('taco_counts')
    for cid in count_ids:
        try:
            response = count_table.update_item(
                Key={
                    'cid': cid
                },
                UpdateExpression="set #attrName = #attrName + :attrValue",
                ExpressionAttributeNames={
                    "#attrName": tou
                },
                ExpressionAttributeValues={
                    ':attrValue': decimal.Decimal(1)
                },
                ReturnValues="NONE"
            )
            print(response)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                # Creating new top level attribute `info` (with nested props)
                # if the previous query failed
                response = count_table.update_item(
                    Key={
                        'cid': cid
                    },
                    UpdateExpression="set #attrName = :attrValue",
                    ExpressionAttributeNames={
                        "#attrName": tou
                    },
                    ExpressionAttributeValues={
                        ':attrValue': decimal.Decimal(1)
                    },
                    ReturnValues="NONE"
                )
                print(response)
            else:
                raise

    return

def dynamo_get_recents(team, days=0):
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('taco_transactions')

    by_person = {}

    for day_back in range(days, -1, -1):
        cid = get_cid_back(team, day_back)
        date = cid[0:10]
        response = table.query(
            IndexName='cid-index',
            KeyConditionExpression=Key('cid').eq(cid)
        )
        for record in response.get("Items", []):
            person_data = by_person.setdefault(record['to_display_name'], {}).setdefault(date, [])
            person_data.append(record)

    return by_person

def dynamo_get_leaderboard(cid):
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('taco_counts')

    # Get Requested Leaderboard
    response = table.query(
        KeyConditionExpression=Key('cid').eq(cid)
    )
    counts = response['Items'][0]
    del counts['cid']

    # Convert to list and sort
    count_tups = []
    for key, value in counts.iteritems():
        count_tups.append((key, int(value)))

    count_tups.sort(key=lambda s: s[1], reverse=True)

    # Cut list to 10
    if len(count_tups) > 10:
        count_tups = count_tups[:10]

    return count_tups


def dynamo_get_tacos_avail(user):
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('taco_transactions')

    response = table.scan(
        IndexName='from-timestamp-index',
        Select='COUNT',
        FilterExpression=Key('from').eq(user) & Key('timestamp').gte(get_epoch(get_local_midnight()))
    )

    print(response)
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


def get_cid_this_month(team):
    midnight = get_local_midnight()
    return midnight.strftime('%Y-M%m') + "-" + team


def get_cid_this_week(team):
    midnight = get_local_midnight()
    return midnight.strftime('%Y-W%U') + "-" + team


def get_cid_this_year(team):
    midnight = get_local_midnight()
    return midnight.strftime('%Y') + "-" + team


def get_cid_back(team, back):
    midnight = get_local_midnight() - datetime.timedelta(days=back)
    return midnight.strftime('%Y-%m-%d') + "-" + team

def get_cid_today(team):
    midnight = get_local_midnight()
    return midnight.strftime('%Y-%m-%d') + "-" + team

def get_epoch(ts):
    return int(((ts - datetime.datetime(1970, 1, 1)) - datetime.timedelta(hours=int(timezone))).total_seconds())


def get_local_midnight():
    st = datetime.datetime.now() + datetime.timedelta(hours=int(timezone))
    midnight = datetime.datetime(st.year, st.month, st.day, 0, 0, 0)
    return midnight


def get_team_name():
    params = {"token": bot_token}
    r = requests.get('https://slack.com/api/team.info', params=params)
    team_info = r.json()

    return team_info['team']['name']

def get_user_display_name(user_id):
    params = {"token": bot_token, "user": user_id}
    r = requests.get('https://slack.com/api/users.info', params=params)
    user_info = r.json()

    return user_info['user']['name']

def get_channel_display_name(channel_id):
    params = {"token": bot_token, "channel": channel_id}
    r = requests.get('https://slack.com/api/conversations.info', params=params)
    channel_info = r.json()

    return channel_info['channel']['name']

def get_channel_members(channel_id):
    params = {"token": bot_token, "channel": channel_id}
    r = requests.get('https://slack.com/api/conversations.members', params=params)
    channel_info = r.json()

    return set(channel_info['members'])

def get_time_to_next_midnight():
    st = datetime.datetime.now() + datetime.timedelta(hours=int(timezone))
    next_midnight = datetime.datetime(st.year, st.month, st.day, 0, 0, 0) + datetime.timedelta(hours=24)
    return next_midnight - st


def get_user_name(user_id):
    params = {"token": bot_token, "user": user_id}
    r = requests.get('https://slack.com/api/users.info', params=params)
    user_info = r.json()

    return user_info['user']['name']


def process_tacos(tc, tu, tr, body):
    index = 1
    from_user_display_name = get_user_display_name(body['event']['user'])
    channel_display_name = get_channel_display_name(body['event']['channel'])
    for user in tu:
        for x in range(tc):
            user_display_name = get_user_display_name(user)
            dynamo_add_taco(body['event']['event_ts'], index, body['team_id'], 
                            body['event']['channel'], channel_display_name,
                            body['event']['user'], from_user_display_name, user, user_display_name,
                            body['event']['text'])
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


def send_message_recent(channel, team, users_in_channel=None):
    days = 7
    recents_by_user = dynamo_get_recents(team, days)

    channel_members = None
    if users_in_channel is not None:
        channel_members = get_channel_members(users_in_channel)

    message = "Recent %d days\n\n" % days
    for user, by_day in recents_by_user.iteritems():
        for day, items in by_day.iteritems():
            if channel_members is not None and items[0]["to"] not in channel_members:
                continue

            message += "@%s received %d:\n" % (user, len(items))

            for item in items:
                for_string = item["message"]
                if "to_display_name" in item:
                    for_string = for_string.replace('<@%s>' % item.get("to"), '@' + item["to_display_name"])
                if "from_display_name" in item:
                    for_string = for_string.replace('<@%s>' % item.get("from"), '@' + item["from_display_name"])
                message += "%s in #%s from @%s for '%s'\n" % (day, item["channel_display_name"], item["from_display_name"], for_string)

    attachment = "[{\"text\": \"" + message + "\"}]"
    send_slack_message(None, channel, attachment)

def send_message_leaderboard(channel, team, time_range):
    leaderboard = []
    message = "*"

    if time_range == 'daily':
        message = message + "Today's "
        leaderboard = dynamo_get_leaderboard(get_cid_today(team))
    elif time_range == 'monthly':
        message = message + "This Month's "
        leaderboard = dynamo_get_leaderboard(get_cid_this_month(team))
    elif time_range == 'yearly':
        message = message + "This Year's "
        leaderboard = dynamo_get_leaderboard(get_cid_this_year(team))
    else:
        message = message + "This Week's "
        leaderboard = dynamo_get_leaderboard(get_cid_this_week(team))

    message = message + get_team_name()
    message = message + " Leaderboard*\n"

    index = 1
    for leader in leaderboard:
        message = message + str(index) + "). " + get_user_name(leader[0]) + " `" + str(leader[1]) + "`\n"
        index = index + 1

    attachment = "[{\"text\": \"" + message + "\"}]"
    send_slack_message(None, channel, attachment)


def send_message_not_enough_tacos(user, tried, tr, channel):
    p = inflect.engine()
    delta = get_time_to_next_midnight()
    delta_values = divmod(delta.days * 86400 + delta.seconds, 60)

    hours = delta_values[0] / 60
    minutes = delta_values[0] % 60

    text = "Whoops! You tried to give *" + str(tried) + "* " + p.plural(taco_name, tried) + ". You have *" + str(tr) + \
           "* " + p.plural(taco_name, tr) + " left to give today. Your " + p.plural(taco_name) + \
           " will reset in *"

    if hours > 0:
        text = text + str(hours) + " hours and "

    text = text + str(minutes) + " minutes*."

    send_slack_ephemeral(text, channel, user)


def send_message_tacos_available(user, tr):
    p = inflect.engine()
    delta = get_time_to_next_midnight()
    delta_values = divmod(delta.days * 86400 + delta.seconds, 60)

    hours = delta_values[0] / 60
    minutes = delta_values[0] % 60

    text = "You have *" + str(tr) + "* " + p.plural(taco_name, tr) + " left to give today. Your " + \
           p.plural(taco_name) + " will reset in *"

    if hours > 0:
        text = text + str(hours) + " hours and "

    text = text + str(minutes) + " minutes*."

    send_slack_message(text, user)


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


def send_slack_ephemeral(message, channel, user):
    params = {"token": bot_token, "text": message, "channel": channel, "user": user, "as_user": True}

    r = requests.get('https://slack.com/api/chat.postEphemeral', params=params)


def send_slack_message(message, channel, attachment=None):
    params = {"token": bot_token, "text": message, "channel": channel, "as_user": True}
    if attachment != None:
        params['attachments'] = attachment

    r = requests.get('https://slack.com/api/chat.postMessage', params=params)


def slack_message(body):
    # Find taco in channel messages
    if (body['event']['channel_type'] == 'channel' or body['event']['channel_type'] == 'group') and 'text' in body['event']:
        taco_count = find_taco(body['event']['text'])
        myself_re = re.compile(r':' + re.escape(taco_name) + r':')

        if taco_count > 0:
            if debug == 'true': print("Found " + str(taco_count) + " taco(s)")
            taco_users = find_users(body['event']['text'], body['event']['user'])
            if len(taco_users) > 0:
                my_tacos_avail = dynamo_get_tacos_avail(body['event']['user'])
                if debug == 'true': print("you have " + str(my_tacos_avail) + " taco(s)")

                taco_tries = taco_count * len(taco_users)
                if my_tacos_avail >= taco_tries:
                    if debug == 'true': print("you can give these tacos")
                    process_tacos(taco_count, taco_users, my_tacos_avail, body)
                else:
                    send_message_not_enough_tacos(body['event']['user'], taco_tries, my_tacos_avail,
                                                  body['event']['channel'])
        elif body['event']['text'].find("<@" + bot_user + "> ") != -1:
            if body['event']['text'].find("leaderboard") != -1:
                if debug == 'true': print("found leaderboard in channel")
                if body['event']['text'].find("leaderboard weekly") != -1:
                    send_message_leaderboard(body['event']['channel'], body['team_id'], 'weekly')
                elif body['event']['text'].find("leaderboard daily") != -1 or body['event']['text'].find("leaderboard today") != -1:
                    send_message_leaderboard(body['event']['channel'], body['team_id'], 'daily')
                elif body['event']['text'].find("leaderboard monthly") != -1:
                    send_message_leaderboard(body['event']['channel'], body['team_id'], 'monthly')
                elif body['event']['text'].find("leaderboard yearly") != -1:
                    send_message_leaderboard(body['event']['channel'], body['team_id'], 'yearly')
                else:
                    send_message_leaderboard(body['event']['channel'], body['team_id'], 'weekly')

    elif body['event']['channel_type'] == 'im' and 'bot_id' not in ['event']:
        if debug == 'true': print("got im: " + body['event']['text'])
        p = inflect.engine()
        if body['event']['text'] == p.plural(taco_name):
            my_tacos_avail = dynamo_get_tacos_avail(body['event']['user'])
            send_message_tacos_available(body['event']['user'], my_tacos_avail)
        elif body['event']['text'] in ('leaderboard', 'leaderboard weekly'):
            send_message_leaderboard(body['event']['user'], body['team_id'], 'weekly')
        elif body['event']['text'] in ('leaderboard daily', 'leaderboard today'):
            send_message_leaderboard(body['event']['user'], body['team_id'], 'daily')
        elif body['event']['text'] == 'leaderboard monthly':
            send_message_leaderboard(body['event']['user'], body['team_id'], 'monthly')
        elif body['event']['text'] == 'leaderboard yearly':
            send_message_leaderboard(body['event']['user'], body['team_id'], 'yearly')
        elif body['event']['text'].startswith('recent'):
            args = body['event']['text'].split(' ')
            if len(args) > 1 and args[1].startswith('<#'):
                channel_filter = re.match('<#([^\|>]*)', args[1]).group(1)
            else:
                channel_filter = None
            send_message_recent(body['event']['user'], body['team_id'], channel_filter)

    return


# main
def lambda_handler(event, context):
    midnight = datetime.datetime.now() + datetime.timedelta(hours=int(timezone))
    print(midnight.strftime('%Y-%m-%d %H:%M:%S'))
    print(get_epoch(midnight))

    for record in event['Records']:
        # Get POST body
        try:
            body = json.loads(record['Sns']['Message'])
        except ValueError as e:
            return respond(e)

        # Route Body
        if debug == 'true':
            print("Got body: " + json.dumps(body, indent=2))

        slack_message(body)

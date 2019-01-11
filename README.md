# yotaco
Blatant heytaco rip off

## required AWS resources

- A lambda to receive web hooks (POST requests) from Slack. Typically called 'yotaco-webhook'

- A lambda to process messages sent from the web hook processer via SNS. Typically called 'yotaco-msg_processor'
    - Set timeout to AT LEAST 10 seconds

- An SNS queue for messages from the webhook to be processed by the message processor 

- Two dynamo db tables 

    - taco_transactions
        - primary partition key: tid String
        - Secondary index 'from-timestamp-index'
            - primary partition key: from String
            - primary sort key: timestamp Number
        - Secondary index 'cid-index'
            - primary partition key: cid String

    - taco_counts
        - primary partition key: cid String

## Slack configuration

- Create a new app

- Add a bot user to the app

- Required OAuth scopes:

  - channels:history
  - bot
  - users:read
  - channels:read

- Add an event subscription to 'message.channels'

- Add a bot event subscription to 'message.im'

## webhook
handles slack event webhook

### ENV vars
| Key               | Description                                   | Default  |
| ----------------- | --------------------------------------------- | -------- |
| DEBUG             | enable verbose logging                        | false    |
| EMOJI             | text of the slack emoji to use as taco        | taco     |
| MSG_PROC_ARN      | arn of sns that calls msg_processor           |          |
| SLACK_VERIF_TOKEN | slack app verification token                  |          |

## msg_processor
handles slack message processing

### ENV vars
| Key               | Description                                                              | Default  |
| ----------------- | ------------------------------------------------------------------------ | -------- |
| DEBUG             | enable verbose logging                                                   | false    |
| EMOJI             | text of the slack emoji to use as taco                                   | taco     |
| SLACK_BOT_TOKEN   | slack bot token for api                                                  |          |
| TZ_OFFSET         | timezone offset in hours, positive or negative integer (e.g. -8 for PST) | 0        |

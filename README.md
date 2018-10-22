# yotaco
Blatant heytaco rip off

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
| Key               | Description                                   | Default  |
| ----------------- | --------------------------------------------- | -------- |
| DEBUG             | enable verbose logging                        | false    |
| EMOJI             | text of the slack emoji to use as taco        | taco     |
| SLACK_BOT_TOKEN   | slack bot token for api                       |          |
| TZ_OFFSET         | timezone offset, positive or negative integet | 0        |
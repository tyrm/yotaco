# yotaco [![Build Status](https://travis-ci.org/tyrm/yotaco.svg?branch=master)](https://travis-ci.org/tyrm/yotaco)
Blatant heytaco rip off

## webhook
handles slack events

### ENV vars
| Key               | Description                                   | Default  |
| ----------------- | --------------------------------------------- | -------- |
| DEBUG             | enable verbose logging                        | false    |
| EMOJI             | text of the slack emoji to use as taco        | taco     |
| SLACK_BOT_TOKEN   | slack bot token for api                       |          |
| SLACK_VERIF_TOKEN | slack app verification token                  |          |
| TZ_OFFSET         | timezone offset, positive or negative integet | 0        |
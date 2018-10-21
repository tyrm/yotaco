#!/usr/bin/env bash

# Zip it up
rm -Rvf lambda-webhook.zip
cd webhook
pip install -r requirements.txt -t ./
zip -r ../lambda-webhook.zip * -x *.pyc -x *_test.py
cd ..

# Put it in AWS
aws lambda update-function-code --function-name yotaco-webhook --zip-file fileb://lambda-webhook.zip

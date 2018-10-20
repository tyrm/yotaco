#!/usr/bin/env bash

# Zip it up
rm -Rvf lambda-webhook.zip
cd webhook
zip -r ../lambda-webhook.zip *
cd ..

# Put it in AWS
aws lambda update-function-code --function-name api-test-2 --zip-file fileb://lambda-webhook.zip

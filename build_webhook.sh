#!/usr/bin/env bash

# Zip it up
rm -Rvf lambda-webhook.zip
cd webhook
#pip install -r requirements.txt -t ./
zip -9 -r ../lambda-webhook.zip * -x *.pyc -x *_test.py
cd ..

aws s3 cp lambda-webhook.zip s3://ph-builds/lambda-webhook.zip

# Put it in AWS
aws lambda update-function-code --function-name yotaco-webhook --s3-bucket ph-builds --s3-key lambda-webhook.zip

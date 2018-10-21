#!/usr/bin/env bash

# Zip it up
rm -Rvf lambda-msg_processor.zip
cd msg_processor
pip install -r requirements.txt -t ./
zip -9 -r ../lambda-msg_processor.zip * -x *.pyc -x *_test.py
cd ..

aws s3 cp lambda-msg_processor.zip s3://ph-builds/lambda-msg_processor.zip

# Put it in AWS
aws lambda update-function-code --function-name yotaco-msg_processor --s3-bucket ph-builds --s3-key lambda-msg_processor.zip

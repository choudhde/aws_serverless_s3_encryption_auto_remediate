####
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
####
__author__ = 'dc'

import boto3
from botocore.exceptions import ClientError
import os
import time
import random

# Global variables
AWS_REGION = 'ca-central-1'

TOPIC_NAME = str(os.getenv('TOPIC_NAME'))
SNS_SUBJECT = str(os.getenv('SNS_SUBJECT'))
SNS_MESSAGE = str(os.getenv('SNS_MESSAGE'))
SNS_SUBSCRIBER = str(os.getenv('SNS_SUBSCRIBER'))


#####################################
# SNS Topic Creation and Subscription
#####################################

def sns_topic(sns_client):
    sns_topic_arn = sns_client.create_topic(Name=TOPIC_NAME)['TopicArn']
    print("SNS Topic ARN {}".format(sns_topic_arn))
    try:
        sns_list_sub = sns_client.list_subscriptions_by_topic(TopicArn=sns_topic_arn)[
            'Subscriptions']
        if sns_list_sub[0]['SubscriptionArn'] == 'PendingConfirmation':
            print("Subscription is in pending status to the Endpoint: {}".format(
                SNS_SUBSCRIBER))
        elif sns_list_sub[0]['SubscriptionArn'] != 'PendingConfirmation' \
                and sns_list_sub[0]['Endpoint'] == SNS_SUBSCRIBER:
            print("Subscriber already registered {}".format(
                sns_list_sub[0]['SubscriptionArn']))
    except Exception as e:
        print("There's no Subscription to the SNS Topic")
        subscription_arn = sns_client.subscribe(TopicArn=sns_topic_arn, Protocol='email',
                                                Endpoint=SNS_SUBSCRIBER)
        print("Subscription ARN {}".format(
            subscription_arn['SubscriptionArn']))

    return sns_topic_arn


##########################################
# SNS Publish Message to the SNS Topic ARN
##########################################

def sns_publish_message(sns_client, sns_topic_arn, bucket_name):
    aws_account_number = sns_topic_arn.split(":")[4]
    sns_client.publish(TopicArn=sns_topic_arn,
                       Message=SNS_MESSAGE + bucket_name + " in Account:" + aws_account_number,
                       Subject=SNS_SUBJECT)


# ######################################################
# Apply AES:256 if encryption is missing
# ######################################################

def change_bucket_encryption(s3_client, bucket_name):
    try:
        s3_client.put_bucket_encryption(Bucket=bucket_name,
                                        ServerSideEncryptionConfiguration={'Rules':
                                                                           [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]})
        print("Successfully applied encryption AES:256 to bucket: {}".format(bucket_name))
    except Exception as e:
        print("Unexpected Error {}".format(e))


#########################
# Lambda/script entrypoint
#########################

def lambda_handler(event, context):
    try:
        bucket_name = event["detail"]["requestParameters"]["bucketName"]
        # Clients
        sns_client = boto3.client('sns', region_name=AWS_REGION)
        s3_client = boto3.client('s3', region_name=AWS_REGION)

        check_bucket_encryption = s3_client.get_bucket_encryption(
            Bucket=bucket_name)
        print(f'Bucket {bucket_name} has encryption')

    except ClientError as e:
        if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
            print("Bucket {} has no encryption".format(bucket_name))
            sns_topic_arn = sns_topic(sns_client)
            sns_publish_message(sns_client, sns_topic_arn, bucket_name)
            change_bucket_encryption(s3_client, bucket_name)
        else:
            print("Unexpected error: %s" % e)


# If ran on the CLI, go ahead and run it
if __name__ == "__main__":
    lambda_handler({}, {})

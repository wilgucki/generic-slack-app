import json
import logging
import os
from urllib.parse import parse_qsl

import boto3
import requests
from slack_utils import signature, challenge


logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

SLACK_TYPE_COMMAND = 'command'
SLACK_TYPE_APP = 'app'


def slack_app_handler(event, context):
    resource = event['resource'].strip('/')
    logger.info(f'Received {resource}')

    if resource == 'slash-command':
        body = dict(parse_qsl(event['body']))
        sns_topic = os.environ['SLASH_COMMAND_TOPIC_ARN']
    elif resource == 'action-endpoint':
        body = json.loads(event['body'])
        sns_topic = os.environ['SLACK_APP_TOPIC_ARN']
    else:
        raise ValueError(f'Unknown resource: {event["resource"]}')

    ssm_client = boto3.client('ssm')

    if resource == 'action-endpoint' and body['event']['type'] == 'url_verification':
        logger.info('Respond to challenge request')
        token_name = os.environ['SSM_VERIFICATION_TOKEN_NAME']

        verification_token = ssm_client.get_parameter(Name=token_name, WithDecryption=True)
        os.environ['SLACK_VERIFICATION_TOKEN'] = verification_token['Parameter']['Value']

        response = challenge.respond(body['challenge'], body['token'])
        return response

    secret_name = os.environ['SSM_SECRET_NAME']
    signing_secret = ssm_client.get_parameter(Name=secret_name, WithDecryption=True)

    logger.info('Verify message signature')
    signature.verify(
        event['headers']['X-Slack-Signature'],
        event['headers']['X-Slack-Request-Timestamp'],
        event['body'],
        signing_secret['Parameter']['Value']
    )

    logger.info('Publish message to SNS topic')
    sns = boto3.client('sns')
    sns.publish(TargetArn=sns_topic, Message=json.dumps(body))

    return {'statusCode': 200}


def slash_command_worker(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        message = json.loads(body['Message'])

        if 'response_url' in message:

            # process message and replace this generic response with something more adequate
            requests.post(
                message['response_url'],
                headers={'Content-type': 'application/json'},
                data=json.dumps({'text': 'it works!', 'response_type': 'ephemeral'})
            )
        else:
            # TODO send response
            pass


def slack_app_worker(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        message = json.loads(body['Message'])

        # TODO handle message

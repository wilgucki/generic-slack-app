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
    if event['resource'] == '/slash-command':
        body = dict(parse_qsl(event['body']))
    elif event['resource'] == '/action-endpoint':
        body = json.loads(event['body'])
    else:
        raise ValueError(f'Unknown resource: {event["resource"]}')

    ssm_client = boto3.client('ssm')

    if event['resource'] == '/action-endpoint' and body['event']['type'] == 'url_verification':
        token_name = os.environ['SSM_VERIFICATION_TOKEN_NAME']

        verification_token = ssm_client.get_parameter(Name=token_name, WithDecryption=True)
        os.environ['SLACK_VERIFICATION_TOKEN'] = verification_token['Parameter']['Value']

        response = challenge.respond(body['challenge'], body['token'])
        return response

    secret_name = os.environ['SSM_SECRET_NAME']
    signing_secret = ssm_client.get_parameter(Name=secret_name, WithDecryption=True)

    signature.verify(
        event['headers']['X-Slack-Signature'],
        event['headers']['X-Slack-Request-Timestamp'],
        event['body'],
        signing_secret['Parameter']['Value']
    )

    logging.info('adding message to the queue')
    sqs_client = boto3.client('sqs')
    sqs_client.send_message(QueueUrl=os.environ['QUEUE_URL'], MessageBody=json.dumps(body))

    logging.info('acknowledge message')

    return {"statusCode": 200}


def queue_worker(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])

        if 'response_url' in body:  # slash command
            # TODO process message
            requests.post(
                body['response_url'],
                headers={'Content-type': 'application/json'},
                data=json.dumps({'text': 'Thanks for your request, we\'ll process it and get back to you.'})
            )
        else:
            # TODO send response
            pass

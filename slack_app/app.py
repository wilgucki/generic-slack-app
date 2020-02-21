import json
import logging
import os
from urllib.parse import parse_qsl

import boto3
import requests
from slack_utils import signature, challenge


logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', logging.INFO))

SLACK_TYPE_COMMAND = 'command'
SLACK_TYPE_APP = 'app'


def slack_app_handler(event, context):
    logger.info('## EVENT')
    logger.info(event)

    if event['resource'] == '/slash-command':
        body = dict(parse_qsl(event['body']))
    elif event['resource'] == '/action-endpoint':
        body = json.loads(event['body'])
    else:
        raise ValueError(f'Unknown resource: {event["resource"]}')

    logger.info('## BODY')
    logger.info(body)

    ssm_client = boto3.client('ssm')

    if event['resource'] == '/action-endpoint' and body['event']['type'] == 'url_verification':
        verification_token = ssm_client.get_parameter(Name='SLACK_APP_SLACK_VERIFICATION_TOKEN', WithDecryption=True)
        os.environ['SLACK_VERIFICATION_TOKEN'] = verification_token['Parameter']['Value']

        response = challenge.respond(body['challenge'], body['token'])
        logger.info('## SLACK CHALLENGE RESPONSE')
        logger.info(response)
        return response

    signing_secret = ssm_client.get_parameter(Name='SLACK_APP_SLACK_SIGNING_SECRET', WithDecryption=True)

    signature.verify(
        event['headers']['X-Slack-Signature'],
        event['headers']['X-Slack-Request-Timestamp'],
        event['body'],
        signing_secret['Parameter']['Value']
    )

    logging.info('adding message to the queue')
    sqs_client = boto3.client('sqs')
    sqs_client.send_message(
        QueueUrl=os.environ['QUEUE_URL'],
        MessageBody=json.dumps(body)
    )

    logging.info('acknowledge message')

    return {
        "statusCode": 200
    }


def queue_worker(event, context):
    logger.info('## EVENT')
    logger.info(event)

    for record in event['Records']:
        body = json.loads(record['body'])
        logger.info('## BODY')
        logger.info(body)

        if 'response_url' in body:  # slash command
            requests.post(
                body['response_url'],
                headers={'Content-type': 'application/json'},
                data=json.dumps({'text': 'Thanks for your request, we\'ll process it and get back to you.'})
            )
        else:
            # TODO send response
            pass

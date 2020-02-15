import json
import logging
import os
from urllib.parse import parse_qsl

import boto3
from slack_utils import signature, challenge


logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', logging.INFO))

SLACK_TYPE_COMMAND = 'command'
SLACK_TYPE_APP = 'app'


def slash_command_handler(event, context):
    logger.info('## EVENT')
    logger.info(event)

    ssm_client = boto3.client('ssm')
    signing_secret = ssm_client.get_parameter(Name='SLACK_APP_SLACK_SIGNING_SECRET', WithDecryption=True)

    signature.verify(
        event['headers']['X-Slack-Signature'],
        event['headers']['X-Slack-Request-Timestamp'],
        event['body'],
        signing_secret['Parameter']['Value']
    )

    body = dict(parse_qsl(event['body']))

    logger.info('## SLASH COMMAND BODY')
    logger.info(body)

    logging.info('add a message to the queue')
    sqs_client = boto3.client('sqs')
    sqs_client.send_message(
        QueueUrl=os.environ['QUEUE_URL'],
        MessageBody=json.dumps({
            'type': SLACK_TYPE_COMMAND,
            'body': json.dumps(body),
        })
    )

    logging.info('acknowledge message')

    return {
        "statusCode": 200
    }


def slack_event_handler(event, context):
    logger.info('## EVENT')
    logger.info(event)

    body = json.loads(event['body'])

    logger.info('## BODY')
    logger.info(body)

    ssm_client = boto3.client('ssm')

    if 'type' in body and body['type'] == 'url_verification':
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

    logging.info('add a message to the queue')
    sqs_client = boto3.client('sqs')
    sqs_client.send_message(
        QueueUrl=os.environ['QUEUE_URL'],
        MessageBody=json.dumps({
            'type': SLACK_TYPE_APP,
            'body': json.dumps(body),
        })
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
        # TODO process message based on type

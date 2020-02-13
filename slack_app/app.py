import json
import logging
import os
from urllib.parse import parse_qsl

from slack_utils import signature, challenge


logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', logging.INFO))


def slash_command_handler(event, context):
    logger.info('## EVENT')
    logger.info(event)

    signature.verify(
        event['headers']['X-Slack-Signature'],
        event['headers']['X-Slack-Request-Timestamp'],
        event['body']
    )

    body = dict(parse_qsl(event['body']))

    logger.info('## SLASH COMMAND BODY')
    logger.info(body)

    # handle slash command here
    # body['command']
    # body['text']

    return {
        "statusCode": 200,
        "body": "hello world",  # TODO change this to something meaningful
    }


def slack_event_handler(event, context):
    logger.info('## EVENT')
    logger.info(event)

    body = json.loads(event['body'])

    logger.info('## BODY')
    logger.info(body)

    if 'type' in body and body['type'] == 'url_verification':
        response = challenge.respond(body['challenge'], body['token'])
        logger.info('## SLACK CHALLENGE RESPONSE')
        logger.info(response)
        return response

    signature.verify(
        event['headers']['X-Slack-Signature'],
        event['headers']['X-Slack-Request-Timestamp'],
        event['body']
    )

    # handle app/bot here

    return {
        "statusCode": 200,
        "body": "hello world",  # TODO change this to something meaningful
    }

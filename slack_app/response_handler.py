import json

import requests


class SlashCommandResponseHandler:
    def __init__(self, command, text, response_url, **kwargs):
        self.command = command
        self.text = text
        self.response_url = response_url
        self.kwargs = kwargs
        self.message = None

    def process_input(self):
        # process command and text args and build message
        self.message = f'Received command *{self.command}* with args: *{self.text}*'

    def send_response(self):
        response_type = self.kwargs.get('response_type', 'ephemeral')

        requests.post(
            self.response_url,
            headers={'Content-type': 'application/json'},
            data=json.dumps({'text': self.message, 'response_type': response_type})
        )

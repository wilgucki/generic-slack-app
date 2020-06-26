# Generic Slack App

This is Slack app template I'm using for building Slack apps/bots.

Generic Slack App uses AWS Lambda as a handler and API Gateway to route request to that
handler.

**There's still lot to do, e.g. tests, permissions, etc. I would not consider this
project as production ready, nor should you.**

## How to use it

* `sam build --use-container`
* `sam deploy --guided` --guided option is required only the first time, all subsequent runs should not use it
* [create slack app](https://api.slack.com/apps?new_app=1)
* if asked for url use `sam deploy` command output
* enjoy

import os
import re
# Use the package we installed
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import okta


# loads in env variables - bot & slack token
load_dotenv()
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]  # for ngrok
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]  # for socket
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

app = App(token=SLACK_BOT_TOKEN)


# listens for bot mentions and responds to queries
@app.event("app_mention")
def mention_handler(body, say):
    sender_id = body["event"]["user"]
    say("Hi there <@{}>, let me check for you".format(sender_id))
    response = okta.answerLookup(body['event']['text'])
    # print(body)
    say(response)
    return


# to handle message event
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)


# Starts app, creates socket
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
    # app.start(port=int(os.environ.get("PORT", 3000)))  # enable if using ngrok


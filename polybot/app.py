import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import flask
from flask import request
import os

from telebot.types import Update

from polybot.bot import Bot, QuoteBot, ImageProcessingBot

app = flask.Flask(__name__)
from dotenv import load_dotenv
load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_APP_URL = os.getenv("BOT_APP_URL")
#TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
#BOT_APP_URL = os.environ['BOT_APP_URL']


@app.route('/', methods=['GET'])
def index():
    return 'Ok'



@app.route(f'/{TELEGRAM_BOT_TOKEN}/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = Update.de_json(json_str)
    bot.telegram_bot_client.process_new_updates([update])
    return 'Ok'

if __name__ == "__main__":
    bot = ImageProcessingBot(TELEGRAM_BOT_TOKEN, BOT_APP_URL)

    app.run(host='0.0.0.0', port=8443)

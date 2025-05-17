import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img
from telebot.types import Message
import requests

class Bot:
    def __init__(self, token, telegram_chat_url):
        self.telegram_bot_client = telebot.TeleBot(token)
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)
        print(f"Setting webhook to: {telegram_chat_url}/{token}/")
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)
        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return bool(msg.photo)

    def download_user_photo(self, msg):
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg.photo[-1].file_id)
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")
        self.telegram_bot_client.send_photo(chat_id, InputFile(img_path))

    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')
        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):
    def __init__(self, token, telegram_chat_url):
        super().__init__(token, telegram_chat_url)
        self.concat_pending = {}

        @self.telegram_bot_client.message_handler(func=lambda message: True, content_types=["text", "photo"])
        def handle_all(message: Message):
            self.handle_message(message)

    def predict_image_with_yolo(self, image_path):
        yolo_url = "http://10.0.4.0:8080/predict"
        with open(image_path, 'rb') as img:
            files = {'file': img}
            response = requests.post(yolo_url, files=files)
            return response.json()

    def handle_message(self, msg: Message):
        logger.info(f'Incoming message: {msg}')
        chat_id = msg.chat.id

        if not self.is_current_msg_photo(msg):
            self.send_text(chat_id, "Please send a photo with one of the following captions:\n"
                                    "Blur, Contour, Rotate, Segment, Salt and pepper, Detect")
            return

        caption = (msg.caption or "").strip().lower()
        if not caption:
            self.send_text(chat_id, "Please include a caption for the filter.")
            return

        try:
            photo_path = self.download_user_photo(msg)
            print("Photo saved at:", photo_path)
            img = Img(photo_path)

            if caption == "blur":
                img.blur()
            elif caption == "concat":
                if chat_id in self.concat_pending:
                    try:
                        first_img = self.concat_pending.pop(chat_id)
                        second_img = Img(photo_path)
                        result_img = first_img.concat(second_img)
                        result_path = result_img.save_img()
                        self.send_photo(chat_id, result_path)
                    except Exception as e:
                        self.send_text(chat_id, f"Concat failed: {e}")
                else:
                    self.concat_pending[chat_id] = Img(photo_path)
                    self.send_text(chat_id,
                                   "First image received. Now send the second image with caption 'Concat' to merge.")
                return
            elif caption == "contour":
                img.contour()
            elif caption == "rotate":
                img.rotate()
            elif caption == "segment":
                self.segment = img.segment()
            elif caption == "salt and pepper":
                img.salt_n_pepper()
            elif caption == "detect":
                yolo_url = "http://10.0.4.0:8080/predict"
                files = {'file': open(photo_path, 'rb')}
                response = requests.post(yolo_url, files=files)

                if response.ok:
                    predictions = response.json().get('labels', [])
                    print("YOLO RESPONSE JSON:", response.json())
                    result_text = "Detected objects: " + ', '.join(predictions)
                    self.send_text(chat_id, result_text)
                else:
                    self.send_text(chat_id, f"Detection failed: {response.status_code}")
                return
            else:
                self.send_text(chat_id,
                               "Unsupported caption. Try one of: Blur, Contour, Rotate, Segment, Salt and pepper, Concat, Detect")
                return

            result_path = img.save_img()
            print("Sending image from:", result_path)
            self.send_photo(chat_id, result_path)

        except Exception as e:
            import traceback
            print("Error occurred:", e)
            traceback.print_exc()
            self.send_text(chat_id, "Something went wrong. Please try again.")

import re
import logging
import random
from pathlib import Path

import yaml
import requests
import vk_api
from vk_api import audio
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from pytils import numeral

from recognizer import Recognizer
from functions import decline


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR.joinpath("config.yaml")
VK_CONFIG_PATH = BASE_DIR.joinpath("vk_config.v2.json")

with open(CONFIG_PATH, encoding="utf-8") as ymlFile:
    config = yaml.load(ymlFile.read(), Loader=yaml.Loader)

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)

logger = logging.getLogger('vk_api')
logger.disabled = True


class Utils:
    def shazam(self, url, chat_id):
        song = recognizer.recognize(url)

        if song:
            self.get_audio(query=song, chat_id=chat_id)
        else:
            bot.messages.send(
                chat_id=chat_id,
                message="Не удалось распознать песню :(",
                random_id=get_random_id()
            )

    def get_audio(self, query, chat_id):
        try:
            response = vk_audio.search(q=query, count=1)
            song = list(response)[0]
            attachment = "audio{}_{}".format(song.get("owner_id"), song.get("id"))
            bot.messages.send(
                attachment=attachment,
                chat_id=chat_id,
                random_id=get_random_id()
            )
        except Exception as e:
            bot.messages.send(
                message="Аудиозаписи не найдены :(",
                chat_id=chat_id,
                random_id=get_random_id()
            )

    def get_popular_audio(self, chat_id):
        popular_songs = list(vk_audio.get_popular_iter())
        song = random.choice(popular_songs)
        attachment = "audio{}_{}".format(song["owner_id"], song["id"])
        bot.messages.send(
            attachment=attachment,
            chat_id=chat_id,
            random_id=get_random_id()
        )

    def get_user_albums(self, user_id, chat_id):
        user_info = bot.users.get(
            user_ids=user_id,
            fields="sex"
        )[0]

        decline_username = decline(
            first_name=user_info["first_name"],
            last_name=user_info["last_name"],
            sex=user_info["sex"]
        )

        if user_info["is_closed"]:
            # Профиль закрыт
            message = "Профиль [id{}|{}] закрыт❌".format(user_id, decline_username)
        else:
            # Профиль открыт
            user_albums = vk_audio.get_albums(owner_id=user_id)
            if len(user_albums) != 0:
                # Есть хотя бы один альбом
                message = "У [id{}|{}] {}\n".format(
                    user_id,
                    decline_username,
                    numeral.get_plural(len(user_albums), "альбом, альбома, альбомов")
                )
                album_number = 1
                for album in user_albums:
                    message += "{}. {}\n".format(
                        album_number,
                        album["title"]
                    )
                    album_number += 1
            else:
                message = "У [id{}|{}] нет альбомов".format(user_id, decline_username)

        bot.messages.send(
            chat_id=chat_id,
            message=message,
            random_id=get_random_id()
        )


class Bot:
    def check_message(self, message, chat_id, event):
        if message == "шазам":
            if event.message.fwd_messages:
                if len(event.message.fwd_messages[0]["attachments"]) > 0:
                    # Проверяем, чтобы в пересланном сообщении было голосовое сообщение
                    audio_url = event.message["fwd_messages"][0]["attachments"][0]["audio_message"]["link_mp3"]
                    utils.shazam(audio_url, chat_id)
            elif "reply_message" in event.message:
                if len(event.message.reply_message["attachments"]) > 0:
                    # Проверяем, чтобы в пересланном сообщении было голосовое сообщение
                    audio_url = event.message.reply_message["attachments"][0]["audio_message"]["link_mp3"]
                    utils.shazam(audio_url, chat_id)
        elif message[:7] == "!поиск ":
            query = message[7:]
            utils.get_audio(query=query, chat_id=chat_id)
        elif message == "!популярное":
            utils.get_popular_audio(chat_id)
        elif re.match(r"!альбомы \[id\d+\|(@|)\w+\]", message):
            user_id = int(re.findall(r"!альбомы \[id(\d+)\|(@|)\w+\]", message)[0][0])
            self.is_album_select = utils.get_user_albums(user_id, chat_id)

    def listen(self):
        while True:
            try:
                for event in longpoll.listen():
                    if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
                        message = event.message.text.lower()
                        self.check_message(message=message, chat_id=event.chat_id, event=event)
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                print(e)
                logging.info("Перезапуск бота")

    def run(self):
        logging.info("Бот запущен")
        self.listen()


if __name__ == "__main__":
    authorize = vk_api.VkApi(token=config["group"]["group_token"])
    longpoll = VkBotLongPoll(
        authorize,
        group_id=config["group"]["group_id"]
    )

    bot = authorize.get_api()

    vk_session = vk_api.VkApi(
        login=config["user"]["login"],
        password=config["user"]["password"]
    )

    vk_session.auth()
    vk = vk_session.get_api()
    vk_audio = audio.VkAudio(vk_session)

    VK_CONFIG_PATH.unlink()

    recognizer = Recognizer()
    recognizer.auth(config)

    vkbot = Bot()
    utils = Utils()
    
    logging.info("Авторизация прошла успешно")

    vkbot.run()
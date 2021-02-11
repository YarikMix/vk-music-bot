# -*- coding: utf-8 -*-
import random

import vk_api
from vk_api import audio
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import yaml
from pytils import numeral

from functions import decline

popular_listening = []

with open("config.yaml") as ymlFile:
    config = yaml.load(ymlFile.read(), Loader=yaml.Loader)

def auth():
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

    try:
        vk_session.auth()
        vk = vk_session.get_api()
        vk_audio = audio.VkAudio(vk_session)

        return {
            "longpoll": longpoll,
            "bot": bot,
            "vk": vk,
            "vk_audio": vk_audio
        }
    except Exception as e:
        print("Не получилось авторизоваться. Неверный логин или пароль.")
        exit()


class Audio(object):
    def __init__(self, bot, vk_audio):
        self.bot = bot
        self.vk_audio = vk_audio

    def get_audio(self, chat_id, query):
        r = self.vk_audio.search(
            q=query,
            count=1
        )
        try:
            song = [song for song in r][0]
            attachment = "audio{}_{}".format(song.get("owner_id"), song.get("id"))
            self.bot.messages.send(
                chat_id=chat_id,
                message="",
                attachment=attachment,
                random_id=get_random_id()
            )
        except:
            self.bot.messages.send(
                chat_id=chat_id,
                message="Аудиозаписи не найдены",
                random_id=get_random_id()
            )

    def get_popular_audio(self, chat_id):
        r = self.vk_audio.get_popular_iter(
            offset=random.randint(1, 50)
        )
        try:
            for song in r:
                attachment = "audio{}_{}".format(song.get("owner_id"), song.get("id"))
                self.bot.messages.send(
                    chat_id=chat_id,
                    message="",
                    attachment=attachment,
                    random_id=get_random_id()
                )
                break
        except:
            self.bot.messages.send(
                chat_id=chat_id,
                message="Аудиозаписи не найдены",
                random_id=get_random_id()
            )

    def get_user_albums(self, chat_id, user_id):
        user = self.bot.users.get(user_ids=user_id)[0]
        decline_username = decline(
            first_name=user["first_name"],
            last_name=user["last_name"]
        )
        if user["is_closed"]:
            # Профиль закрыт
            self.bot.messages.send(
                chat_id=chat_id,
                message="Профиль [id{}|{}] закрыт❌".format(
                    user_id,
                    decline_username
                ),
                random_id=get_random_id()
            )
        else:
            # Профиль открыт
            user_albums = self.vk_audio.get_albums(
                owner_id=user_id
            )
            if len(user_albums) != 0:
                # Хотя бы один альбом есть
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

                self.bot.messages.send(
                    chat_id=chat_id,
                    message=message,
                    random_id=get_random_id()
                )
            else:
                self.bot.messages.send(
                    chat_id=chat_id,
                    message="У [id{}|{}] нет альбомов".format(
                        user_id,
                        decline_username
                    ),
                    random_id=get_random_id()
                )


class Bot(object):
    def __init__(self, longpoll, bot):
        self.longpoll = longpoll
        self.bot = bot

    def check_message(self, received_message, chat_id):
        if received_message[:7] == "!поиск ":
            query = received_message[7:]
            Audio.get_audio(chat_id, query=query)
        elif received_message == "!популярное":
            Audio.get_popular_audio(chat_id)
        elif received_message[:10] == "!аудио [id":
            user_id = int(received_message[10:19])
            self.is_album_select = Audio.get_user_albums(chat_id, user_id)
        elif received_message[:12] == "!аудио [club":
            self.bot.messages.send(
                chat_id=chat_id,
                message="Данная команда не работает с группами",
                random_id=get_random_id()
            )

    def run(self):
        print("Начинаю мониторинг сообщений...")

        """Отслеживаем каждое событие в беседе."""
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and event.message.get("text") != "":
                received_message = event.message.get("text").lower()
                self.from_id = event.message.get("from_id")
                self.check_message(received_message, event.chat_id)


if __name__ == "__main__":
    auth_data = auth()

    VkBot = Bot(
        longpoll=auth_data["longpoll"],
        bot=auth_data["bot"]
    )

    Audio = Audio(
        bot=auth_data["bot"],
        vk_audio=auth_data["vk_audio"]
    )

    VkBot.run()
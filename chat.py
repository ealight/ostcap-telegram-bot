import telebot

from keyboard import PageableInlineKeyboard
from storage import rooms


class User:
    def __init__(self, id, first_name, last_name, current_chat):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.current_chat = current_chat


class Room:
    def __init__(self, bot: telebot.TeleBot, user: User, admin: User, topic: str):
        self.bot = bot
        self.user = user
        self.admin = admin
        self.topic = topic
        self.active = False
        self.chat_id = user.id

    def connect(self):
        self.bot.send_message(self.user.id, "Адміністоратор підлючився")
        self.bot.send_message(self.admin.id, f"Ви підключились до чату {self.chat_id}")

        self.user.current_chat = self.chat_id
        self.admin.current_chat = self.chat_id
        self.active = True

    def start(self):
        full_username = f"{self.user.first_name} {self.user.last_name}"
        chat_keyboard = PageableInlineKeyboard(bot=self.bot, chat_id=self.admin.id,
                                               button_action=connect_to_chat_action,
                                               callback="connect",
                                               message=f"Користувач {full_username} хоче задати питання по '{self.topic}'.",
                                               data=["Підключитись"], button_callback=lambda _: self.user.id)
        chat_keyboard.send()
        self.bot.send_message(self.user.id, "Адміністратор повинен до вас підключитись. Очікуйте")

    def create_disconnect_button(self, chat_id: int, text: str):
        return PageableInlineKeyboard(bot=self.bot, chat_id=chat_id,
                                      button_action=disconnect_from_chat_action,
                                      callback="disconnect",
                                      message=text,
                                      data=["Відключитись"], button_callback=lambda _: self.user.id)


def disconnect_from_chat_action(query):
    room_id = int(query.data.strip("disconnect:"))

    if room_id in rooms:
        room = rooms[room_id]

        if room.active:
            if query.from_user.id == room.admin.id:
                room.bot.send_message(room.user.id, f"Адміністратор покинув чат")
                room.bot.send_message(room.admin.id, f"Ви покинули чат {room.user.id}")
            if query.from_user.id == room.user.id:
                room.bot.send_message(room.admin.id, "Користувач покинув чат")
                room.bot.send_message(room.user.id, f"Ви покинули чат")

            room.user.current_chat = None
            room.admin.current_chat = None
            room.active = False

            del rooms[room_id]


def connect_to_chat_action(query):
    room_id = int(query.data.strip("connect:"))

    for active_room in rooms.values():
        if query.message.chat.id == active_room.admin.id:
            active_room.active = False

    if room_id in rooms:
        room = rooms[room_id]
        room.connect()

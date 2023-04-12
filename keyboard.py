import uuid
from typing import Callable

import telebot
from telebot import types


class StaticKeyboardButton:
    def __init__(self, text: str, handler: Callable):
        self.text = text
        self.handler = handler


class StaticKeyboard:

    def __init__(self, bot: telebot.TeleBot, chat_id: int, rows: list[list[str]], message):
        self.bot = bot
        self.chat_id = chat_id
        self.rows = rows
        self.message = message

    def create(self):
        self.bot.send_message(self.chat_id, self.message, reply_markup=self.__keyboard())

    def __keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        for row in self.rows:
            markup.row(*[types.KeyboardButton(text) for text in row])
        return markup


class PageableInlineKeyboard:
    __default_page = 0
    __default_per_page = 5
    __prev_handle_word, __next_handle_word = "prev", "next"

    def __init__(self, bot: telebot.TeleBot, chat_id,
                 callback: str, message: str, data: list,
                 button_action: Callable,
                 button_text: Callable = lambda item: item,
                 button_callback: Callable = lambda item: item):
        self.bot = bot
        self.callback = callback
        self.chat_id = chat_id
        self.message = message

        self.data = data
        self.button_text = button_text
        self.button_callback = button_callback

        self.page = self.__default_page
        self.per_page = self.__default_per_page
        self.keyboard_id = uuid.uuid4()

        self.bot.callback_query_handler(func=self.__navigation_handler(self.__prev_handle_word))(self.__prev_page)
        self.bot.callback_query_handler(func=self.__navigation_handler(self.__next_handle_word))(self.__next_page)
        self.bot.callback_query_handler(func=self.__button_callback_handler())(button_action)

    def send(self):
        self.bot.send_message(self.chat_id, self.message,
                              reply_markup=self.__keyboard())

    def __keyboard(self):
        current_page = self.page * self.per_page
        current_per_page = current_page + self.per_page

        markup = types.InlineKeyboardMarkup()
        for item in self.data[current_page:current_per_page]:
            markup.add(types.InlineKeyboardButton(self.button_text(item),
                                                  callback_data=f"{self.callback}:{self.button_callback(item)}"))

        if current_per_page < len(self.data):
            markup.add(
                types.InlineKeyboardButton("Дальше",
                                           callback_data=f"{self.keyboard_id}:{self.__next_handle_word}:{self.page}"))

        if self.page > 0:
            markup.add(
                types.InlineKeyboardButton("Назад",
                                           callback_data=f"{self.keyboard_id}:{self.__prev_handle_word}:{self.page}"))

        return markup

    def __next_page(self, query):
        self.page = self.page + 1
        self.bot.edit_message_reply_markup(chat_id=self.chat_id, message_id=query.message.message_id,
                                           reply_markup=self.__keyboard())

    def __prev_page(self, query):
        self.page = self.page - 1
        self.bot.edit_message_reply_markup(chat_id=self.chat_id, message_id=query.message.message_id,
                                           reply_markup=self.__keyboard())

    def __button_callback_handler(self):
        return lambda call: call.data.startswith(f"{self.callback}:")

    def __navigation_handler(self, action: str):
        return lambda call: call.data.startswith(f"{self.keyboard_id}:{action}:")

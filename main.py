import os

import telebot
from telebot import types

from chat import Room, User
from keyboard import PageableInlineKeyboard, StaticKeyboard
from storage import users, rooms

bot = telebot.TeleBot(os.environ.get('TELEGRAM_TOKEN'))

faq_quest = {
    "Question1": "Answer1",
    "Question2": "Answer2",
    "Question3": "Answer1",
    "Question4": "Answer2",
    "Question5": "Answer1",
    "Question6": "Answer2",
    "Question7": "Answer1",
    "Question8": "Answer2",
    "Question9": "Answer1",
    "Question10": "Answer2",
    "Question11": "Answer1",
    "Question12": "Answer2",
}


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    rows = [["Питання/Відповідь", "Написати"]]
    start_keyboard = StaticKeyboard(bot, message.chat.id, rows, "Виберіть опцію:")
    start_keyboard.create()


@bot.message_handler(content_types=['text'], func=lambda message: message.text == "Питання/Відповідь")
def faq_handler(message: types.Message):
    faq_keyboard = PageableInlineKeyboard(bot=bot, chat_id=message.chat.id,
                                          button_action=faq_action,
                                          callback="faq", message="Виберіть питання:", data=list(faq_quest.keys()))
    faq_keyboard.send()


def faq_action(query):
    question = str(query.data.strip("faq:"))
    bot.send_message(query.from_user.id, faq_quest[question])
    bot.answer_callback_query(query.id)


contact_options = {
    "Донат на армію": [{'name': 'Адмін1', 'id': 6075930616}, {'name': 'Адмін2', 'id': 31313131}],
    "Інше": [{'name': 'Адмін3', 'id': 13431341}]
}


@bot.message_handler(content_types=['text'], func=lambda message: message.text == "Написати")
def contact_handler(message: types.Message):
    faq_keyboard = PageableInlineKeyboard(bot=bot, chat_id=message.chat.id,
                                          button_action=contact_action,
                                          callback="contact", message="По якому питанню:",
                                          data=list(contact_options.keys()))
    faq_keyboard.send()


def contact_action(query):
    option_key = str(query.data.strip("contact:"))
    option = contact_options[option_key]
    option_keyboard = PageableInlineKeyboard(bot=bot, chat_id=query.message.chat.id,
                                             button_action=choose_admin_action,
                                             callback="choose_admin", message="Виберіть людину зі списку:",
                                             data=option, button_text=lambda admin: admin['name'],
                                             button_callback=lambda admin: f"{admin['id']}:{option_key}")
    option_keyboard.send()
    bot.answer_callback_query(query.id)


def choose_admin_action(query):
    contact = query.data.strip("choose_admin:")
    (admin_id, topic) = contact.split(":")
    message = query.message
    chat_id = message.chat.id

    if int(admin_id) not in users:
        admin = User(int(admin_id), 'Admin', 'Admin', None)
    else:
        admin = users[int(admin_id)]

    if chat_id not in users:
        user = User(chat_id, message.chat.first_name, message.chat.last_name, None)
    else:
        user = users[chat_id]

    room = Room(bot, user, admin, topic)
    room.start()
    rooms[chat_id] = room


@bot.message_handler(
    content_types=['animation', 'audio', 'contact', 'dice', 'document', 'location', 'photo', 'poll', 'sticker',
                   'text', 'venue', 'video', 'video_note', 'voice'])
def wild_message_handler(message: types.Message):
    chat_id = message.chat.id

    for room in rooms.values():
        if room.active:
            if chat_id == room.admin.id:
                proxy_message = room.create_disconnect_button(room.user.id, text=message.text)
                proxy_message.send()
            elif chat_id == room.user.id:
                proxy_message = room.create_disconnect_button(room.admin.id, text=message.text)
                proxy_message.send()


bot.infinity_polling(skip_pending=True)

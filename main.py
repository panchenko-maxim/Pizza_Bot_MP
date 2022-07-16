from misc import TOKEN
from telebot import TeleBot
from classes.user import User
from db.db import connect
from business_handlers import *


bot = TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    User.create_user_if_it_not_db(message.chat.id)
    bot.delete_message(message.chat.id, message.message_id)
    main_menu(User.get_by_id(message.chat.id, bot))


@bot.message_handler(commands=['admin'])
def admin(message):
    User.create_user_if_it_not_db(message.chat.id)
    bot.delete_message(message.chat.id, message.message_id)
    examination(User.get_by_id(message.chat.id, bot))


@bot.message_handler(content_types=['text'])
def text_handler(message):
    user = User.get_by_id(message.chat.id, bot)
    handler = HANDLERS[user.next_message_handler]
    if handler.__code__.co_varnames[-1] == 'text':  # проверяем последний аргумент хендлера == 'text'
        handler(user, message.text)
    bot.delete_message(message.chat.id, message.message_id)


@bot.callback_query_handler(lambda call: True)
def inline_buttons_handler(call):
    user = User.get_by_id(call.message.chat.id, bot)
    HANDLERS[user.next_message_handler](user, call.data)
    bot.answer_callback_query(call.id)


bot.polling()

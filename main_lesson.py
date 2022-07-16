from misc import TOKEN
import sqlite3
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


bot = TeleBot(TOKEN)


class UserNotFoundError(BaseException):
    def __init__(self, chat_id):
        super(f'Не был найден пользователь с chat_id = {chat_id} в базе данных')


def connect():
    conn = sqlite3.connect('db/data.db')
    cursor = conn.cursor()
    return conn, cursor


class User:
    columns = ['id', 'username', 'phone', 'email', 'cur_cart_id', 'bot_message_id', 'next_message_handler']

    def __init__(self, id, username, phone, email, cur_cart_id, bot_message_id, next_message_handler):
        self.id = id
        self.username = username
        self.phone = phone
        self.email = email
        self.cur_cart_id = cur_cart_id
        self.bot_message_id = bot_message_id
        self.next_message_handler = next_message_handler

    @property
    def chat_id(self):
        return self.id

    @classmethod
    def get_by_id(cls, chat_id):
        conn, cursor = connect()
        query = f"SELECT {', '.join(cls.columns)} FROM User_ WHERE id = {chat_id}"
        cursor.execute(query)
        table = cursor.fetchall()
        if len(table) == 0:
            raise UserNotFoundError(chat_id)

        kwargs = {column: value for column, value in zip(cls.columns, table[0])}

        return User(id=kwargs['id'], username=kwargs['username'], phone=kwargs['phone'], email=kwargs['email'],
                   cur_cart_id=kwargs['cur_cart_id'], bot_message_id=kwargs['bot_message_id'],
                   next_message_handler=kwargs['next_message_handler'])

    @classmethod
    def create_user_if_it_is_not_in_db(cls, chat_id):
        conn, cursor = connect()
        cursor.execute(f'SELECT id FROM User_ WHERE id={chat_id}')
        table = cursor.fetchall()
        if len(table) == 0:
            cls.create_default_user(chat_id, conn, cursor)

    @classmethod
    def create_default_user(cls, chat_id, conn, cursor):
        cursor.execute(f"INSERT INTO User_ (id, username) VALUES ({chat_id}, 'New user')")
        conn.commit()

    def save_next_message_handler(self, handler):
        index = HANDLERS.index(handler)
        query = f"UPDATE User_\n" \
                f"SET next_message_handler = {index}\n" \
                f"WHERE id={self.id}"
        conn, cursor = connect()
        cursor.execute(query)
        conn.commit()
        self.next_message_handler = index

    def send_message(self, message, keyboard):

        if self.bot_message_id is None:
            message = bot.send_message(self.id, message, reply_markup=keyboard)
            self.save_bot_message_id(message.message_id)
        else:
            bot.edit_message_text(chat_id=self.id, text=message, message_id=self.bot_message_id, reply_markup=keyboard)

    def save_bot_message_id(self, bot_message_id):
        query = f"UPDATE User_\n" \
                f"SET bot_message_id = {bot_message_id}\n" \
                f"WHERE id={self.id}"
        conn, cursor = connect()
        cursor.execute(query)
        conn.commit()
        self.bot_message_id = bot_message_id


@bot.message_handler(commands=['start'])
def start_handler(message):
    User.create_user_if_it_is_not_in_db(message.chat.id)
    bot.delete_message(message.chat.id, message.message_id)
    main_menu(User.get_by_id(message.chat.id))


@bot.callback_query_handler(lambda call: True)
def inline_buttons_handler(call):
    user = User.get_by_id(call.message.chat.id)
    HANDLERS[user.next_message_handler](user, call.data)
    bot.answer_callback_query(call.id)


def main_menu(user):
    text = f"--= Главное меню =--"
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Заказать пиццу', callback_data='order_pizza'),
                 InlineKeyboardButton('История заказов', callback_data='history'))
    keyboard.row(InlineKeyboardButton('Меню аккаунта', callback_data='account'))
    keyboard.row(InlineKeyboardButton('Документы', callback_data='documents'),
                 InlineKeyboardButton('О нас', callback_data='about'))

    user.send_message(text, keyboard)
    user.save_next_message_handler(main_menu_handler)


def main_menu_handler(user, data):
    menus = {
        'order_pizza': order_pizza_menu,
        'history': history_menu,
        'account': account_menu
    }
    menus[data](user)


def account_menu(user):
    text = f"--= Главное меню =--\n" \
           f"{user.username} (phone: {user.phone})"
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Изменить никнейм', callback_data='nickname_change'),
                 InlineKeyboardButton('Изменить телефон', callback_data='phone_change'))
    keyboard.row(InlineKeyboardButton('Изменить email', callback_data='email_change'))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))

    user.send_message(text, keyboard)
    user.save_next_message_handler(account_menu_handler)


def account_menu_handler(user, data):
    if data == 'back':
        main_menu(user)


def order_pizza_menu(user):
    pass


def history_menu(user):
    pass


HANDLERS = [main_menu_handler, account_menu_handler]


bot.polling()
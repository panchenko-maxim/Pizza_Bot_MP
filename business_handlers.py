from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.db import connect
from tools.pizza_sizes import pizza_sizes
from tools.order_status import order_status
from time import sleep


def main_menu(user):
    text = f'--= Главное меню =--'
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Заказать пицца', callback_data='order_pizza'),
                 InlineKeyboardButton('История заказов', callback_data='history'))
    keyboard.row(InlineKeyboardButton('Меню аккаунта', callback_data='account'))
    keyboard.row(InlineKeyboardButton('Документы', callback_data='documents'),
                 InlineKeyboardButton('О нас', callback_data='about'))

    user.send_message(text, keyboard)
    user.save_next_message_handler(main_menu_handler)


def main_menu_handler(user, data):
    menus = {
        'order_pizza': before_choose_pizza_menu,
        'history': history_menu,
        'account': account_menu,
        'documents': documents_menu,
        'about': about_menu
    }
    menus[data](user)


def account_menu(user):
    text = f'--= Главное меню =--\n' \
           f'{user.username} (phone: {user.phone})'
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Изменить никнейм', callback_data='nickname_change'),
                 InlineKeyboardButton('Изменить телефон', callback_data='phone_change'))
    keyboard.row(InlineKeyboardButton('Изменить email', callback_data='email_change'))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))

    user.send_message(text, keyboard)
    user.save_next_message_handler(account_menu_handler)


def account_menu_handler(user, data):
    {
        'nickname_change': nickname_change_menu,
        'phone_change': phone_change_menu,
        'back': lambda user_: main_menu(user_)
    }[data](user)


def nickname_change_menu(user):
    user.send_message('Введите новый никнейм: ')
    user.save_next_message_handler(nickname_change_menu_handler)


def nickname_change_menu_handler(user, text):
    if 4 <= len(text) <= 20:
        user.save_username(text)
        main_menu(user)
    else:
        user.send_message('Ваш никнейм не подходит. Отправьте новый')


def phone_change_menu(user):
    pass


def before_choose_pizza_menu(user):
    user.recreate_cart()
    user.recreate_order()
    choose_pizza_menu(user)


def create_cart_text(user):
    conn, cursor = connect()
    # Достаем пиццы из корзины пользователя
    query = f"SELECT Pizza.id, Pizza.name, Ingredient.name, Pizza.size FROM User_ " \
            f"JOIN Cart ON User_.cur_cart_id = Cart.id " \
            f"JOIN PizzaCart ON Cart.id  = PizzaCart.cart_id " \
            f"JOIN Pizza ON PizzaCart.pizza_id = Pizza.id " \
            f"JOIN IngredientInPizza ON Pizza.id = IngredientInPizza.pizza_id " \
            f"JOIN Ingredient ON IngredientInPizza.ingredient_id = Ingredient.id " \
            f"WHERE User_.id = {user.id} \n" \
            f"ORDER BY Pizza.id"
    cursor.execute(query)
    table = cursor.fetchall()

    last_pizza_id = None
    cart_text = ''
    text = ''
    for row in table + [(-10, '', '', 1)]:
        if row[0] != last_pizza_id:
            if last_pizza_id is not None:
                cart_text += text[:-2] + ')\n'

            text = row[1] + f' {pizza_sizes[int(row[3])]} ('
            last_pizza_id = row[0]

        text += row[2] + ', '
    return cart_text, conn, cursor


def choose_pizza_menu(user):
    cart_text, conn, cursor = create_cart_text(user)

    # Достаем все прото пиццы
    query = f'SELECT Pizza.id, Pizza.name, Ingredient.name \n' \
            f'FROM Pizza \n' \
            f'JOIN IngredientInPizza ON Pizza.id = IngredientInPizza.pizza_id \n' \
            f'JOIN Ingredient ON Ingredient.id = IngredientInPizza.ingredient_id \n' \
            f'WHERE Pizza.is_proto = 1 \n' \
            f'ORDER BY Pizza.id'
    cursor.execute(query)
    table = cursor.fetchall()

    keyboard = InlineKeyboardMarkup()
    last_pizza_id = None
    text = ''
    for row in table + [(-10, '', '')]:
        if row[0] != last_pizza_id:
            if last_pizza_id is not None:
                keyboard.row(InlineKeyboardButton(text[:-2] + ')', callback_data=last_pizza_id))

            text = row[1] + '('
            last_pizza_id = row[0]

        text += row[2] + ', '

    keyboard.row(InlineKeyboardButton('Конструктор піцци', callback_data='constructor'))
    keyboard.row(InlineKeyboardButton('Корзина', callback_data='cart'),
                 InlineKeyboardButton('Оформити замовлення', callback_data='order'))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))
    user.send_message(f'Ваша корзина:\n{cart_text}\n\nВиберіть піцу', keyboard)
    user.save_next_message_handler(choose_pizza_menu_handler)


def choose_pizza_menu_handler(user, data):
    if data == 'cart':
        return cart_menu(user)
    if data == 'back':
        return main_menu(user)

    if data == 'order':
        return order_menu(user)

    conn, cursor = connect()
    cursor.execute(f'UPDATE User_ SET cur_pizza_id=? WHERE id = {user.id}', (data,))
    conn.commit()
    user.cur_pizza_id = data
    choose_pizza_size_menu(user, data)


def cart_menu(user):
    cart_text, conn, cursor = create_cart_text(user)
    query = f"SELECT Pizza.id, Pizza.name, Pizza.size FROM User_ " \
            f"JOIN Cart ON User_.cur_cart_id = Cart.id " \
            f"JOIN PizzaCart ON Cart.id  = PizzaCart.cart_id " \
            f"JOIN Pizza ON PizzaCart.pizza_id = Pizza.id " \
            f"WHERE User_.id = {user.id} \n" \
            f"ORDER BY Pizza.id"
    cursor.execute(query)
    table = cursor.fetchall()
    cart_text = 'Корзина пуста' if len(cart_text) == 0 else cart_text

    keyboard = InlineKeyboardMarkup()
    for i, pizza in enumerate(table, start=1):
        keyboard.row(InlineKeyboardButton(f"{i}) Видалити: {pizza[1]} - {pizza_sizes[pizza[2]]}", callback_data=f"{pizza[0]}"))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))

    user.send_message(cart_text, keyboard)
    user.save_next_message_handler(cart_menu_handler)


def cart_menu_handler(user, data):
    if data == 'back':
        return choose_pizza_menu(user)
    conn, cursor = connect()
    conn.execute(f'DELETE FROM PizzaCart WHERE pizza_id = {data}')
    conn.commit()
    cart_menu(user)


def choose_pizza_size_menu(user, pizza_id):
    conn, cursor = connect()
    query = f'SELECT Pizza.name, Ingredient.name, IngredientInPizza.grams \n' \
            f'FROM Pizza \n' \
            f'JOIN IngredientInPizza ON Pizza.id = IngredientInPizza.pizza_id \n' \
            f'JOIN Ingredient ON Ingredient.id = IngredientInPizza.ingredient_id\n' \
            f'WHERE Pizza.id = ?'
    cursor.execute(query, (pizza_id,))
    table = cursor.fetchall()

    text = f'Ваша піца: {table[0][0]}\n' \
           f'Інгрідієнти:\n'
    for row in table:
        text += f'- {row[1]} ({row[2]} грам)\n'
    text += f'Розмір: {user.cur_chosen_size_name}\n' \
            f'Борт: пустий'

    keyboard = InlineKeyboardMarkup()
    for size in range(1, 4):
        keyboard.row(InlineKeyboardButton(f'змінити розмір: {pizza_sizes[size]}',
                                          callback_data=f"s{size}"))
    # TODO: додати борти піц
    keyboard.row(InlineKeyboardButton(f"Відміна", callback_data='cancel'))
    keyboard.row(InlineKeyboardButton(f"В корзину", callback_data='add'))
    user.send_message(text, keyboard)
    user.save_next_message_handler(choose_pizza_size_menu_handler)


def add_pizza_to_cart(user):
    query = f"INSERT INTO Pizza (name, is_custom, is_proto, size) " \
            f"SELECT name, is_custom, 0, {user.cur_chosen_size} FROM Pizza WHERE id={user.cur_pizza_id};"
    conn, cursor = connect()
    cursor.execute(query)
    conn.commit()
    pizza_copy_id = cursor.lastrowid

    query = f"INSERT INTO IngredientInPizza (ingredient_id, pizza_id, grams) " \
            f"SELECT ingredient_id, {pizza_copy_id}, grams FROM IngredientInPizza WHERE pizza_id={user.cur_pizza_id};"
    cursor.execute(query)
    conn.commit()

    cursor.execute(f"INSERT INTO PizzaCart (cart_id, pizza_id) VALUES ({user.cur_cart_id}, {pizza_copy_id})")
    conn.commit()


def choose_pizza_size_menu_handler(user, data):
    conn, cursor = connect()

    if data == 'cancel':
        return choose_pizza_menu(user)
    if data == 'add':
        add_pizza_to_cart(user)
        return choose_pizza_menu(user)
    if data[0] == 's':
        new_size = data[1]
        cursor.execute(f'UPDATE User_ SET cur_chosen_size = ? WHERE id = {user.id}',
                       (new_size,))
        conn.commit()
        user.cur_chosen_size = new_size
        choose_pizza_size_menu(user, user.cur_pizza_id)


def order_menu(user):
    cart_text, conn, cursor = create_cart_text(user)

    query = f'SELECT * FROM Orders WHERE id = {user.cur_order_id}'
    cursor.execute(query)
    table = cursor.fetchall()[0]

    text = f'Замовлення №: {table[0]}\n' \
           f'Час оформлення: {table[1]}\n' \
           f'Статус: {order_status[int(table[2])]}\n' \
           f'Ціна: {table[3]}\n' \
           f'Адреса: {table[4]}\n\n' \
           f'У корзині:\n' \
           f'{cart_text}'

    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Вказати адресу', callback_data='write_the_address', ))
    keyboard.row(InlineKeyboardButton('Згоден з замовленням. Запустити в роботу', callback_data='put_into_processing'))
    keyboard.row(InlineKeyboardButton('Повернутися до корзини', callback_data='back_to_cart'))
    keyboard.row(InlineKeyboardButton('Зкинути налаштування замовлення та повернутись до головного меню',
                                      callback_data='quit_and_return_to_main_menu'))
    user.send_message(text, keyboard)
    user.save_next_message_handler(order_menu_handler)


def order_menu_handler(user, data):
    if data == 'write_the_address':
        return write_the_address_menu(user)
    elif data == 'put_into_processing':
        user.status_change(2)
        user.send_message("Дякуємо за замовлення! Очікуйте на зворотній зв'язок!")
        sleep(2)
        main_menu(user)
    elif data == 'back_to_cart':
        return choose_pizza_menu(user)
    elif data == 'quit_and_return_to_main_menu':
        return main_menu(user)


def write_the_address_menu(user):
    user.send_message('Будь ласка, напишіть адресу: ')
    user.save_next_message_handler(write_the_address_menu_handler)


def write_the_address_menu_handler(user, text):
    # почему когда тут прописывал напрямую запрос без метода user, программа не шла дальше write_the_address_menu?
    user.save_address(text)
    order_menu(user)


def history_menu(user):
    pass


def documents_menu(user):
    pass


def about_menu(user):
    pass


def examination(user):
    user.send_message('Введіть пароль:')
    user.save_next_message_handler(examination_handler)


def examination_handler(user, text):
    if text == 'admin':
        admin_main_menu(user)
    else:
        user.send_message('Пароль не вірний!')


def admin_main_menu(user):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Замовлення', callback_data='orders'))
    keyboard.row(InlineKeyboardButton('Добавити інгридієнти', callback_data='add_ingredients'))
    keyboard.row(InlineKeyboardButton('Створити піцу', callback_data='create_pizza'))
    user.send_message('!!!***МЕНЮ АДМІНА***!!!', keyboard)
    user.save_next_message_handler(admin_main_menu_handler)


def admin_main_menu_handler(user, data):
    if data == 'orders':
        return admin_orders_menu(user)
    elif data == 'add_ingredients':
        pass
    elif data == 'create_pizza':
        pass


def admin_orders_menu(user):
    conn, cursor = connect()
    quite = 'SELECT * FROM Orders'
    cursor.execute(quite)
    orders = cursor.fetchall()
    text = '-==ЗАМОВЛЕННЯ==-\n\n'
    description = ['№', 'date', 'status', 'price', 'address', 'cart_id', 'user_id']
    keyboard = InlineKeyboardMarkup()
    text_on_button = ''
    callback_button = ''
    for order in orders:
        order_with_description = list(zip(description, order))
        print(order_with_description)
        for i in range(len(order_with_description)):
            if i == 0:
                text_on_button += f"{order_with_description[i][0]}: {order_with_description[i][1]}; "
                callback_button += f"{order_with_description[i][1]}"
            elif i == 2:
                text_on_button += f"{order_with_description[i][0]}: {order_status[order_with_description[i][1]]}; "
            elif i != 1 and 2 < i:
                text_on_button += f"{order_with_description[i][0]}: {order_with_description[i][1]}; "
        keyboard.row(InlineKeyboardButton(text_on_button, callback_data=callback_button))
        text_on_button = ''
        callback_button = ''

    user.send_message(text, keyboard)
    user.save_next_message_handler(admin_orders_menu_handler)


def admin_orders_menu_handler(user, data):
    pass


HANDLERS = [main_menu_handler, account_menu_handler, nickname_change_menu_handler,
            choose_pizza_menu_handler, choose_pizza_size_menu_handler, cart_menu_handler, order_menu_handler,
            write_the_address_menu_handler, examination_handler, admin_main_menu_handler, admin_orders_menu_handler]

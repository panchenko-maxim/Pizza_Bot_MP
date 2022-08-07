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
            f'WHERE Pizza.is_proto = true \n' \
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
    cursor.execute(f'UPDATE User_ SET cur_pizza_id=%s WHERE id = {user.id}', (data,))
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
    cursor.execute(f'DELETE FROM PizzaCart WHERE pizza_id = {data}')
    conn.commit()
    cart_menu(user)


def choose_pizza_size_menu(user, pizza_id):
    conn, cursor = connect()
    query = f'SELECT Pizza.name, Ingredient.name, IngredientInPizza.grams \n' \
            f'FROM Pizza \n' \
            f'JOIN IngredientInPizza ON Pizza.id = IngredientInPizza.pizza_id \n' \
            f'JOIN Ingredient ON Ingredient.id = IngredientInPizza.ingredient_id\n' \
            f'WHERE Pizza.id = %s'
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
            f"SELECT name, is_custom, false, {user.cur_chosen_size} FROM Pizza WHERE id={user.cur_pizza_id} RETURNING id"
    conn, cursor = connect()
    cursor.execute(query)
    conn.commit()
    pizza_copy_id = cursor.fetchone()[0]

    query = f"INSERT INTO IngredientInPizza (ingredient_id, pizza_id, grams) " \
            f"SELECT ingredient_id, {pizza_copy_id}, grams FROM IngredientInPizza WHERE pizza_id={user.cur_pizza_id}"
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
        cursor.execute(f'UPDATE User_ SET cur_chosen_size = %s WHERE id = {user.id}',
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
        # sleep(2)
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
    keyboard.row(InlineKeyboardButton('Інгридієнти', callback_data='ingredients'))
    keyboard.row(InlineKeyboardButton('Піци', callback_data='pizzas'))
    user.send_message('!!!***МЕНЮ АДМІНА***!!!', keyboard)
    user.save_next_message_handler(admin_main_menu_handler)


def admin_main_menu_handler(user, data):
    if data == 'orders':
        admin_orders_menu(user)
    elif data == 'ingredients':
        admin_ingredients_menu(user)
    elif data == 'pizzas':
        admin_pizzas_menu(user)


def admin_orders_menu(user):
    conn, cursor = connect()
    query = 'SELECT * FROM Orders'
    cursor.execute(query)
    orders = cursor.fetchall()
    text = '-==ЗАМОВЛЕННЯ==-\n\n'
    description = ['№', 'date', 'status', 'price', 'address', 'cart_id', 'user_id']
    keyboard = InlineKeyboardMarkup()
    text_on_button = ''
    callback_button = ''
    for order in orders:
        order_with_description = list(zip(description, order))

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
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))

    user.send_message(text, keyboard)
    user.save_next_message_handler(admin_order_menu)


def admin_order_menu(user, data):
    if data == 'back':
        return admin_main_menu(user)
    conn, cursor = connect()
    query = f'SELECT * FROM Orders WHERE id={data}'
    cursor.execute(query)
    order = cursor.fetchall()[0]

    description = ['№', 'date', 'status', 'price', 'address', 'cart_id', 'user_id']
    order_with_description = list(zip(description, order))
    text = ''
    for el in order_with_description:
        if el[0] == 'status':
            text += f"{el[0]}: {order_status[el[1]]}\n"
        else:
            text += f"{el[0]}: {el[1]}\n"

    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Змінити статус замовлення на "виконано"', callback_data=f'admin_change_order_{data}_status'))
    keyboard.row(InlineKeyboardButton('Змінити адресу замовлення', callback_data=f'admin_change_order_{data}_address'))
    keyboard.row(InlineKeyboardButton('Видалити замовлення', callback_data=f'{data}_delete'))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))

    user.send_message(text, keyboard)
    user.save_next_message_handler(admin_order_menu_handler)


def admin_order_menu_handler(user, data):
    conn, cursor = connect()
    if data == 'back':
        admin_orders_menu(user)
    elif data.split('_')[-1] == 'address':
        user.cur_order_id = int(data.split("_")[-2])
        cursor.execute(f"UPDATE User_ SET cur_order_id = {user.cur_order_id} WHERE id={user.id}")
        conn.commit()
        user.send_message('Будь ласка, напишіть адресу: ')
        user.save_next_message_handler(admin_change_the_address_handler)
    else:
        id_order = int(data.split("_")[-2])
        if data.split('_')[-1] == 'delete':
            cursor.execute(f'DELETE FROM Orders WHERE id={id_order}')
        elif data.split('_')[-1] == 'status':
            cursor.execute(f"UPDATE Orders SET status = 3 WHERE id={id_order}")
        conn.commit()
        admin_orders_menu(user)


def admin_change_the_address_handler(user, text):
    user.save_address(text)
    admin_order_menu(user, user.cur_order_id)


def admin_ingredients_menu(user):
    text = "***Меню Інгредієнти***\n"
    query = f"SELECT * FROM Ingredient"
    conn, cursor = connect()
    cursor.execute(query)
    table = cursor.fetchall()
    for el in table:
        text += f"{el[0]}) {el[1]} - {el[2]} грн.\n"
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Видалити інгредієнт', callback_data='delete_ingredient'))
    keyboard.row(InlineKeyboardButton('Створити інгредієнт', callback_data='create_ingredient'))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))
    user.send_message(text, keyboard)
    user.save_next_message_handler(admin_ingredients_menu_handler)


def admin_ingredients_menu_handler(user, data):
    if data == 'back':
        admin_main_menu(user)
    elif data == 'delete_ingredient':
        delete_ingredient_menu(user)
    elif data == 'create_ingredient':
        user.send_message('Напишіть інгредієнт та ціну(цифрами) за 100 грам через пробіл')
        user.save_next_message_handler(create_new_ingredient_handler)


def create_new_ingredient_handler(user, text):
    # new_ingredient = text.split()
    # if new_ingredient[-1].isdigit() and len(new_ingredient) >= 2:
    #     query = f'''INSERT INTO Ingredient (name, price) VALUES ('{" ".join(new_ingredient[:-1])}', {new_ingredient[-1]})'''
    #     conn, cursor = connect()
    #     cursor.execute(query)
    #     conn.commit()
    create_new_ingredient(text)
    admin_ingredients_menu(user)


def create_new_ingredient(text):
    new_ingredient = text.split()
    if new_ingredient[-1].isdigit() and len(new_ingredient) >= 2:
        query = f'''INSERT INTO Ingredient (name, price) VALUES ('{" ".join(new_ingredient[:-1])}', {new_ingredient[-1]})'''
        conn, cursor = connect()
        cursor.execute(query)
        conn.commit()


def delete_ingredient_menu(user):
    conn, cursor = connect()
    query = f"SELECT * FROM Ingredient"
    cursor.execute(query)
    table = cursor.fetchall()
    cart_text = 'Корзина пуста' if len(table) == 0 else 'Інгредієнти'

    keyboard = InlineKeyboardMarkup()
    for el in table:
        keyboard.row(InlineKeyboardButton(f"{el[0]}) Видалити: {el[1]} - {el[2]}", callback_data=f"{el[0]}"))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))

    user.send_message(cart_text, keyboard)
    user.save_next_message_handler(delete_ingredient_menu_handler)


def delete_ingredient_menu_handler(user, data):
    if data == 'back':
        return admin_ingredients_menu(user)
    conn, cursor = connect()
    cursor.execute(f'DELETE FROM Ingredient WHERE id = {data}')
    conn.commit()
    delete_ingredient_menu(user)


def select_proto_true_pizzas_and_create_text():
    conn, cursor = connect()

    # Достаем все прото пиццы
    query = f'SELECT Pizza.id, Pizza.name, Ingredient.name \n' \
            f'FROM Pizza \n' \
            f'JOIN IngredientInPizza ON Pizza.id = IngredientInPizza.pizza_id \n' \
            f'JOIN Ingredient ON Ingredient.id = IngredientInPizza.ingredient_id \n' \
            f'WHERE Pizza.is_proto = true'
    cursor.execute(query)
    table = cursor.fetchall()

    text = ''
    id_now = None

    for row in table:
        if id_now == row[0]:
            text += f"{row[2]}, "
        elif id_now is None:
            id_now = row[0]
            text += f'{row[0]}) {row[1]} ({row[2]}, '
        else:
            id_now = row[0]
            text = text[:-2]
            text += f')\n{row[0]}) {row[1]}({row[2]}, '
    text = text[:-2] + ')'
    return text


def admin_pizzas_menu(user):
    pizzas_text = select_proto_true_pizzas_and_create_text()
    text = '***Піци***\n' + pizzas_text
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Створити піцу', callback_data='create_pizza'))
    keyboard.row(InlineKeyboardButton('Редагувати піцу', callback_data='edit_pizza'))
    keyboard.row(InlineKeyboardButton('Видалити піцу', callback_data='delete_pizza'))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))
    user.send_message(text, keyboard)
    user.save_next_message_handler(admin_pizzas_menu_handler)


def admin_pizzas_menu_handler(user, data):
    if data == 'create_pizza':
        admin_create_pizza_menu_1(user)
    elif data == 'edit_pizza':
        admin_edit_pizza_menu(user)
    elif data == 'delete_pizza':
        admin_delete_pizza_menu(user)
    elif data == 'back':
        admin_main_menu(user)


def admin_create_pizza_menu_1(user):
    query = "INSERT INTO Pizza(name, is_custom, is_proto, size) VALUES('new_pizza', false, true, 1) RETURNING id"
    conn, cursor = connect()
    cursor.execute(query)
    conn.commit()

    user.cur_pizza_id = cursor.fetchone()[0]

    query = f"INSERT INTO IngredientInPizza (ingredient_id, pizza_id, grams) " \
            f"VALUES (1, {user.cur_pizza_id}, 150)"
    cursor.execute(query)
    conn.commit()

    admin_create_pizza_menu_2(user)


def admin_create_pizza_menu_2(user):
    query = f"SELECT Pizza.id, Pizza.name, Ingredient.name \n" \
            f"FROM Pizza \n" \
            f"JOIN IngredientInPizza ON Pizza.id = IngredientInPizza.pizza_id \n" \
            f"JOIN Ingredient ON Ingredient.id = IngredientInPizza.ingredient_id \n" \
            f"WHERE Pizza.id = {user.cur_pizza_id}"
    conn, cursor = connect()
    cursor.execute(query)
    table = cursor.fetchall()[0]

    text = f"id: {table[0]}\nНазва піци: {table[1]}\nІнгредієнти: {', '.join(table[2:])}"
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('Дати назву піци', callback_data='name_the_pizza'))
    keyboard.row(InlineKeyboardButton('Додати інгридієнти', callback_data='add_ingredients'))
    keyboard.row(InlineKeyboardButton('Видалити інгредієнти', callback_data='delete_ingredients'))
    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))
    user.send_message(text, keyboard)
    user.save_next_message_handler(admin_create_pizza_menu_2_handler)


def admin_create_pizza_menu_2_handler(user, data):
    if data == 'back':
        admin_pizzas_menu(user)


def admin_edit_pizza_menu(user):
    pass


def admin_delete_pizza_menu(user):
    pizza_lst = select_proto_true_pizzas_and_create_text().split('\n')
    text = 'Видалити піцу' if len(pizza_lst) != 0 else 'Немає піц для видалення'

    keyboard = InlineKeyboardMarkup()
    for pizza in pizza_lst:
        keyboard.row(InlineKeyboardButton(f'{pizza}', callback_data=f'{pizza[0]}'))

    keyboard.row(InlineKeyboardButton('Назад', callback_data='back'))
    user.send_message(text, keyboard)
    user.save_next_message_handler(admin_delete_pizza_menu_handler)


def admin_delete_pizza_menu_handler(user, data):
    if data == 'back':
        return admin_pizzas_menu(user)
    conn, cursor = connect()
    cursor.execute(f'DELETE FROM Pizza WHERE pizza_id = {data}')
    conn.commit()
    admin_delete_pizza_menu(user)


HANDLERS = [main_menu_handler, account_menu_handler, nickname_change_menu_handler,
            choose_pizza_menu_handler, choose_pizza_size_menu_handler, cart_menu_handler, order_menu_handler,
            write_the_address_menu_handler, examination_handler, admin_main_menu_handler, admin_order_menu,
            admin_order_menu_handler, admin_change_the_address_handler, admin_ingredients_menu_handler,
            create_new_ingredient_handler, delete_ingredient_menu_handler, admin_pizzas_menu_handler,
            admin_delete_pizza_menu_handler, admin_create_pizza_menu_2_handler]

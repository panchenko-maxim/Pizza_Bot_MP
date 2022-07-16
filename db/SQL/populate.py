import sqlite3


def connect():
    conn = sqlite3.connect('../data.db')
    cursor = conn.cursor()
    return conn, cursor


ingredients = [
    {
        'name': 'тісто',
        'price': 6
    },
    {
        'name': 'сир моцарела',
        'price': 40
    },
    {
        'name': 'сир пармезан',
        'price': 100
    },
    {
        'name': 'томат',
        'price': 30
    },
    {
        'name': 'цибуля',
        'price': 30
    },
    {
        'name': 'шампиньони',
        'price': 30
    },
    {
        'name': 'ковбаски баварські',
        'price': 70
    },
    {
        'name': 'ковбаса салямі',
        'price': 80
    },
    {
        'name': 'шинка',
        'price': 65
    },
    {
        'name': 'соус кетчуп',
        'price': 30
    },
    {
        'name': 'соус майонез',
        'price': 35
    },
    {
        'name': 'ананас',
        'price': 50
    },
    {
        'name': 'курка',
        'price': 60
    },
    {
        'name': 'кукурудза',
        'price': 35
    }
]


pizzas = [
    {
        'name': 'Маргарита',
        'ingredients': [
            {
                'ingr': 'тісто',
                'grams': 150
            },
            {
                'ingr': 'соус кетчуп',
                'grams': 50
            },
            {
                'ingr': 'томат',
                'grams': 50
            },
            {
                'ingr': 'сир моцарела',
                'grams': 140
            }
        ]
    },
    {
        'name': 'Гавайська',
        'ingredients': [
            {
                'ingr': 'тісто',
                'grams': 150
            },
            {
                'ingr': 'соус майонез',
                'grams': 50
            },
            {
                'ingr': 'ананас',
                'grams': 120
            },
            {
                'ingr': 'курка',
                'grams': 100
            },
            {
                'ingr': 'сир моцарела',
                'grams': 100
            },
            {
                'ingr': 'кукурудза',
                'grams': 30
            }
        ]
    },
    {
        'name': 'Паппероні',
        'ingredients': [
            {
                'ingr': 'тісто',
                'grams': 150
            },
            {
                'ingr': 'соус кетчуп',
                'grams': 50
            },
            {
                'ingr': 'томат',
                'grams': 50
            },
            {
                'ingr': 'сир моцарела',
                'grams': 140
            },
            {
                'ingr': 'ковбаса салямі',
                'grams': 100
            }
        ]
    }
]


conn, cursor = connect()

for ingr in ingredients:
    cursor.execute(f"INSERT INTO Ingredient (name, price) VALUES (?, ?)", list(ingr.values()))
    conn.commit()


for pizza in pizzas:
    cursor.execute(f"INSERT INTO Pizza (name, is_custom, is_proto, size) VALUES (?, ?, ?, ?)", (pizza['name'],
                                                                                                False, True, 1))
    conn.commit()

    cursor.execute(f"SELECT id FROM Pizza WHERE name=? ", [pizza['name']])
    pizza_id = cursor.fetchall()[0][0]

    for ingr in pizza['ingredients']:
        cursor.execute(f"SELECT id FROM Ingredient WHERE name=? ", [ingr['ingr']])
        ingr_id = cursor.fetchall()[0][0]

        query = f"INSERT INTO IngredientInPizza (ingredient_id, pizza_id, grams) VALUES ({ingr_id}, {pizza_id}, {ingr['grams']})"
        cursor.execute(query)
    conn.commit()

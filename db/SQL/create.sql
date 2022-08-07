CREATE TABLE Ingredient(
    id SERIAL PRIMARY KEY,
    name VARCHAR(30),
    price FLOAT
);

CREATE TABLE Pizza(
    id SERIAL PRIMARY KEY,
    name VARCHAR(20),
    is_custom BOOLEAN,
    is_proto BOOLEAN,
    size INT
);

CREATE TABLE Cart(
    id SERIAL PRIMARY KEY
);

CREATE TABLE User_(
    id BIGSERIAL PRIMARY KEY, -- chat_id
    username VARCHAR(20),
    phone VARCHAR(20) NULL,
    email VARCHAR(30) NULL,
    cur_cart_id INT NULL REFERENCES Cart(id),
    cur_order_id INT NULL,
    bot_message_id INT NULL,
    next_message_handler INT NULL,    -- index of handler in list
    cur_pizza_id INT NULL,
    cur_chosen_size INT DEFAULT 2,
    cur_chosen_side INT DEFAULT 1
);

CREATE TABLE IngredientInPizza(
    ingredient_id INT REFERENCES Ingredient(id),
    pizza_id INT REFERENCES Pizza(id),
    grams INT,
    PRIMARY KEY(ingredient_id, pizza_id)
);

CREATE TABLE PizzaCart(
    cart_id INT REFERENCES Cart(id),
    pizza_id INT REFERENCES Pizza(id),
    PRIMARY KEY(cart_id, pizza_id)
);

CREATE TABLE Orders(
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP DEFAULT NOW(),
    status INT NULL,
    price FLOAT,
    address VARCHAR(50),
    cart_id INT REFERENCES Cart(id),
    user_id BIGINT REFERENCES User_(id)
);
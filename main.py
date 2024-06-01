#===========================================================================
#55.32
import os
import sqlite3
from telebot import TeleBot, types
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# Инициализация бота
bot = TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')
#bot = TeleBot('6992737528:AAEhRgiVOQOtfb0m9RCXbej74r9MP6FaOjQ')


@bot.message_handler(commands=['hellp', 'weather'])
def command_handler(message):
    if message.text == '/hellp':
        bot.send_message(message.chat.id, 'Приветствую вас!\n\nКоманды бота:\n\n/main - вернуться в главное меню\n/hellp - приветствие и помощь\n/weather - открыть сайт погоды\n\nДля запуска бота нажми на\n значёк скрепки, прикрепить фаил: photo'
                                          '\nили импортируй сюда фото\n из галерей своего устройства')
    elif message.text == '/weather':
        weather_link = 'https://yandex.ru/weather/?lat=63.71604156&lon=66.66759491&via=ssc'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)




# Словарь с доступными объектами
object_names = {
    'PRS-10': 'PRS-10',
    'PRS-11': 'PRS-11',
    'UPRS-12': 'UPRS-12',
    'PRS-13': 'PRS-13',
    'KS-5-7': 'KS 5 - 7',
    'UTT-and-ST': 'UTT and ST'
}

# Функции для работы с базой данных
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                chat_id INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_name TEXT,
                photo_id INTEGER,
                message TEXT,
                user_id INTEGER,
                FOREIGN KEY (photo_id) REFERENCES photos(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

def add_user(username, chat_id):
    conn = get_db_connection()
    with conn:
        try:
            conn.execute("INSERT INTO users (username, chat_id) VALUES (?, ?)", (username, chat_id))
        except sqlite3.IntegrityError:
            # Если пользователь уже существует, ничего не делаем
            pass

def add_photo(file_id):
    conn = get_db_connection()
    with conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO photos (file_id) VALUES (?)", (file_id,))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Если фотография уже существует в базе данных, вернем ее ID
            cursor.execute("SELECT id FROM photos WHERE file_id = ?", (file_id,))
            return cursor.fetchone()[0]


def add_item(object_name, photo_id, message, user_id):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("INSERT INTO items (object_name, photo_id, message, user_id) VALUES (?, ?, ?, ?)",
                         (object_name, photo_id, message, user_id))
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            time.sleep(0.5)  # Ожидание перед повторной попыткой
            with conn:
                conn.execute("INSERT INTO items (object_name, photo_id, message, user_id) VALUES (?, ?, ?, ?)",
                             (object_name, photo_id, message, user_id))
        else:
            raise e


# Обработчики команд
@bot.message_handler(commands=['start'])
def start(message):
    user = bot.get_chat(message.chat.id)
    user_id = get_user_id(message.chat.id)
    if not user_id:
        add_user(user.username, message.chat.id)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in ['Добавить',  'Просмотреть', 'Отмена']]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(func=lambda message: message.text in ['Добавить', 'Просмотреть', 'Отмена'])
def handle_menu_option(message):
    if message.text == 'Добавить':
        show_object_selection(message)
    elif message.text == 'Просмотреть':
        show_look_menu(message)
    elif message.text == 'Отмена':
        start(message)

def show_object_selection(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    keyboard.add(*buttons)

    msg = bot.send_message(message.chat.id, "Выберите объект:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_selected_object)

def process_selected_object(message):
    selected_object = message.text
    for key, value in object_names.items():
        if value == selected_object:
            object_name = key
            break
    msg = bot.send_message(message.chat.id, "Введите описание:")
    bot.register_next_step_handler(msg, lambda m: process_message(m, object_name))

def process_message(message, object_name):
    message_text = message.text
    msg = bot.send_message(message.chat.id, "Отправьте фото объекта:")
    bot.register_next_step_handler(msg, lambda m: process_photo(m, object_name, message_text))


def process_photo(message, object_name, message_text):
    if message.photo:
        file_id = message.photo[-1].file_id
        photo_id = add_photo(file_id)
        user_id = get_user_id(message.chat.id)
        add_item(object_name, photo_id, message_text, user_id)

        # Создание клавиатуры с кнопкой "Домой"
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_home = types.KeyboardButton("Домой")
        keyboard.add(button_home)

        # Отправка сообщения с клавиатурой
        bot.reply_to(message, "Данные сохранены.", reply_markup=keyboard)

        # Регистрация обработчика для кнопки "Домой"
        bot.register_next_step_handler(message, start)
    else:
        bot.reply_to(message, "Вы не отправили фото.")


def show_look_menu(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    buttons.append(types.KeyboardButton("Все объекты"))
    buttons.append(types.KeyboardButton("Домой"))
    keyboard.add(*buttons)
    msg = bot.send_message(message.chat.id, "Выберите объект для просмотра:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, look_data)
    bot.register_next_step_handler(msg, start)


@bot.message_handler(commands=['look'])
def look_data(message):
    user_id = get_user_id(message.chat.id)
    if user_id:
        selected_object = message.text
        if selected_object in object_names.values():
            for key, value in object_names.items():
                if value == selected_object:
                    object_name = key
                    break
            filter_data_by_object(message, object_name)
        else:
            filter_data_by_user(message, user_id)
    else:
        bot.send_message(message.chat.id, "Вы не зарегистрированы в системе. Пожалуйста, используйте команду /start.")

def filter_data_by_object(message, object_name):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM items WHERE object_name = ?", (object_name,))
        user_ids = [row[0] for row in cursor.fetchall()]
        for user_id in user_ids:
            cursor.execute("SELECT i.object_name, i.message, p.file_id FROM items i LEFT JOIN photos p ON i.photo_id = p.id WHERE i.object_name = ? AND i.user_id = ?", (object_name, user_id))
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    if row[2]:
                        bot.send_photo(message.chat.id, row[2], caption=f"{row[0]}\n{row[1]}")
                    else:
                        bot.send_message(message.chat.id, f"{row[0]}\nФото: Отсутствует\nЗамечание: {row[1]}")
            else:
                bot.send_message(message.chat.id, f"Нет сохраненных данных для объекта '{object_name}' и пользователя {user_id}.")

def filter_data_by_user(message, user_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT i.object_name, i.message, p.file_id FROM items i LEFT JOIN photos p ON i.photo_id = p.id WHERE i.user_id = ?", (user_id,))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                if row[2]:
                    bot.send_photo(message.chat.id, row[2], caption=f"{row[0]}\n{row[1]}")
                else:
                    bot.send_message(message.chat.id, f"{row[0]}\nФото: Отсутствует\nЗамечание: {row[1]}")
        else:
            bot.send_message(message.chat.id, "Нет сохраненных данных.")

def get_user_id(chat_id):
    conn = get_db_connection()

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None

if __name__ == '__main__':
    create_tables()
    print("Запуск бота...")
    while True:
        try:
            bot.polling(non_stop=True)
        except Exception as e:
            print(f"Ошибка при запуске бота: {e}")
            time.sleep(10)

'''

#=========================================================================

45.67

базовый код

import os
import sqlite3
from telebot import TeleBot, types

# Инициализация бота
bot = TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')

# Словарь с доступными объектами
object_names = {
    'PRS-10': 'PRS-10',
    'PRS-11': 'PRS-11',
    'PRS-12': 'PRS-12',
    'PRS-13': 'PRS-13',
    'KS-5-7': 'KS 5 - 7',
    'UTT-and-ST': 'UTT and ST',
    'Photo': 'Photo'
}

# Функции для работы с базой данных
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                chat_id INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_name TEXT,
                photo_id INTEGER,
                message TEXT,
                user_id INTEGER,
                FOREIGN KEY (photo_id) REFERENCES photos(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

def add_user(username, chat_id):
    conn = get_db_connection()
    with conn:
        try:
            conn.execute("INSERT INTO users (username, chat_id) VALUES (?, ?)", (username, chat_id))
        except sqlite3.IntegrityError:
            # Если пользователь уже существует, ничего не делаем
            pass

def add_photo(file_id):
    conn = get_db_connection()
    with conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO photos (file_id) VALUES (?)", (file_id,))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Если фотография уже существует в базе данных, вернем ее ID
            cursor.execute("SELECT id FROM photos WHERE file_id = ?", (file_id,))
            return cursor.fetchone()[0]

def add_item(object_name, photo_id, message, user_id):
    conn = get_db_connection()
    with conn:
        conn.execute("INSERT INTO items (object_name, photo_id, message, user_id) VALUES (?, ?, ?, ?)", (object_name, photo_id, message, user_id))

# Обработчики команд
@bot.message_handler(commands=['start'])
def start(message):
    user = bot.get_chat(message.chat.id)
    user_id = get_user_id(message.chat.id)
    if not user_id:
        add_user(user.username, message.chat.id)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in ['Добавить', 'Просмотреть']]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(func=lambda message: message.text in ['Добавить', 'Просмотреть'])
def handle_menu_option(message):
    if message.text == 'Добавить':
        show_object_selection(message)
    elif message.text == 'Просмотреть':
        show_look_menu(message)

def show_object_selection(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    keyboard.add(*buttons)

    msg = bot.send_message(message.chat.id, "Выберите объект:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_selected_object)

def process_selected_object(message):
    selected_object = message.text
    for key, value in object_names.items():
        if value == selected_object:
            object_name = key
            break
    msg = bot.send_message(message.chat.id, "Введите описание:")
    bot.register_next_step_handler(msg, lambda m: process_message(m, object_name))

def process_message(message, object_name):
    message_text = message.text
    msg = bot.send_message(message.chat.id, "Отправьте фото объекта:")
    bot.register_next_step_handler(msg, lambda m: process_photo(m, object_name, message_text))

def process_photo(message, object_name, message_text):
    if message.photo:
        file_id = message.photo[-1].file_id
        photo_id = add_photo(file_id)
        user_id = get_user_id(message.chat.id)
        add_item(object_name, photo_id, message_text, user_id)
        bot.reply_to(message, "Данные сохранены.")
    else:
        bot.reply_to(message, "Вы не отправили фото.")

def show_look_menu(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    buttons.append(types.KeyboardButton("Все объекты"))
    keyboard.add(*buttons)
    msg = bot.send_message(message.chat.id, "Выберите объект для просмотра:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, look_data)

@bot.message_handler(commands=['look'])
def look_data(message):
    user_id = get_user_id(message.chat.id)
    if user_id:
        selected_object = message.text
        if selected_object in object_names.values():
            for key, value in object_names.items():
                if value == selected_object:
                    object_name = key
                    break
            filter_data_by_object(message, object_name)
        else:
            filter_data_by_user(message, user_id)
    else:
        bot.send_message(message.chat.id, "Вы не зарегистрированы в системе. Пожалуйста, используйте команду /start.")

def filter_data_by_object(message, object_name):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT i.object_name, i.message, p.file_id FROM items i LEFT JOIN photos p ON i.photo_id = p.id WHERE i.object_name = ? AND i.user_id = ?", (object_name, get_user_id(message.chat.id)))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                if row[2]:
                    bot.send_photo(message.chat.id, row[2], caption=f"{row[0]}\n{row[1]}")
                else:
                    bot.send_message(message.chat.id, f"{row[0]}\nФото: Отсутствует\nЗамечание: {row[1]}")
        else:
            bot.send_message(message.chat.id, f"Нет сохраненных данных для объекта '{object_name}'.")

def filter_data_by_user(message, user_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT i.object_name, i.message, p.file_id FROM items i LEFT JOIN photos p ON i.photo_id = p.id WHERE i.user_id = ?", (user_id,))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                if row[2]:
                    bot.send_photo(message.chat.id, row[2], caption=f"{row[0]}\n{row[1]}")
                else:
                    bot.send_message(message.chat.id, f"{row[0]}\nФото: Отсутствует\nЗамечание: {row[1]}")
        else:
            bot.send_message(message.chat.id, "Нет сохраненных данных.")

def get_user_id(chat_id):
    conn = get_db_connection()

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None

if __name__ == '__main__':
    create_tables()
    bot.polling(none_stop=True)



#===========================================================================
#7.14
#теперь это основной код, пляшим от него


import os
import sqlite3
from telebot import TeleBot, types

# Инициализация бота
bot = TeleBot('6992737528:AAEhRgiVOQOtfb0m9RCXbej74r9MP6FaOjQ')

# Словарь с доступными объектами
object_names = {
    'PRS-10': 'PRS-10',
    'PRS-11': 'PRS-11',
    'PRS-12': 'PRS-12',
    'PRS-13': 'PRS-13',
    'KS-5-7': 'KS 5 - 7',
    'UTT-and-ST': 'UTT and ST',
    'Photo': 'Photo'
}

# Функции для работы с базой данных
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                chat_id INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_name TEXT,
                photo_id INTEGER,
                message TEXT,
                user_id INTEGER,
                FOREIGN KEY (photo_id) REFERENCES photos(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

def add_user(username, chat_id):
    conn = get_db_connection()
    with conn:
        try:
            conn.execute("INSERT INTO users (username, chat_id) VALUES (?, ?)", (username, chat_id))
        except sqlite3.IntegrityError:
            # Если пользователь уже существует, ничего не делаем
            pass

def add_photo(file_id):
    conn = get_db_connection()
    with conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO photos (file_id) VALUES (?)", (file_id,))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Если фотография уже существует в базе данных, вернем ее ID
            cursor.execute("SELECT id FROM photos WHERE file_id = ?", (file_id,))
            return cursor.fetchone()[0]

def add_item(object_name, photo_id, message, user_id):
    conn = get_db_connection()
    with conn:
        conn.execute("INSERT INTO items (object_name, photo_id, message, user_id) VALUES (?, ?, ?, ?)", (object_name, photo_id, message, user_id))

# Обработчики команд
@bot.message_handler(commands=['start'])
def start(message):
    user = bot.get_chat(message.chat.id)
    user_id = get_user_id(message.chat.id)
    if not user_id:
        add_user(user.username, message.chat.id)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in ['Добавить', 'Просмотреть']]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(func=lambda message: message.text in ['Добавить', 'Просмотреть'])
def handle_menu_option(message):
    if message.text == 'Добавить':
        show_object_selection(message)
    elif message.text == 'Просмотреть':
        look_data(message)

def show_object_selection(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    keyboard.add(*buttons)
    msg = bot.send_message(message.chat.id, "Выберите объект:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_selected_object)


def process_selected_object(message):
    selected_object = message.text
    for key, value in object_names.items():
        if value == selected_object:
            object_name = key
            break
    msg = bot.send_message(message.chat.id, "Введите описание:")
    bot.register_next_step_handler(msg, lambda m: process_message(m, object_name))


def process_message(message, object_name):
    message_text = message.text
    msg = bot.send_message(message.chat.id, "Отправьте фото объекта:")
    bot.register_next_step_handler(msg, lambda m: process_photo(m, object_name, message_text))


def process_photo(message, object_name, message_text):
    if message.photo:
        file_id = message.photo[-1].file_id
        photo_id = add_photo(file_id)
        user_id = get_user_id(message.chat.id)
        add_item(object_name, photo_id, message_text, user_id)
        bot.reply_to(message, "Данные сохранены.")
    else:
        bot.reply_to(message, "Вы не отправили фото.")


@bot.message_handler(commands=['look'])
def look_data(message):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT i.object_name, i.message, p.file_id FROM items i LEFT JOIN photos p ON i.photo_id = p.id WHERE i.user_id = (SELECT id FROM users WHERE chat_id = ?)",
            (message.chat.id,))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                if row[2]:
                    bot.send_photo(message.chat.id, row[2], caption=f"{row[0]}\n{row[1]}")
                else:
                    bot.send_message(message.chat.id, f"{row[0]}\nФото: Отсутствует\nЗамечание: {row[1]}")
        else:
            bot.send_message(message.chat.id, "Нет сохраненных данных")


def get_user_id(chat_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None


if __name__ == '__main__':
    create_tables()
    bot.polling()


#=================================================================================================================
6.35
import telebot
import webbrowser
import sqlite3
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')

# Создание подключения к базе данных SQLite
def get_db_connection():
    return sqlite3.connect('weather.db')

@bot.message_handler(commands=['hellp', 'weather', 'main'])
def command_handler(message):
    if message.text == '/hellp':
        bot.send_message(message.chat.id, 'Приветствую вас!\n\nКоманды бота:\n\n/main - вернуться в главное меню\n/hellp - приветствие и помощь\n/weather - открыть сайт погоды\n\nДля запуска бота нажми на\n значёк скрепки, прикрепить фаил: photo'
                                          '\nили импортируй сюда фото\n из галерей своего устройства')
    elif message.text == '/weather':
        weather_link = 'https://yandex.ru/weather/?lat=63.71604156&lon=66.66759491&via=ssc'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)
    elif message.text == '/main':
        main(message)

@bot.message_handler(commands=['start', 'main', 'hello'])
def main(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')

@bot.message_handler(content_types=['photo'])
def weather_callback(message):
    weather_buttons = [
        types.InlineKeyboardButton('ПРС-10', callback_data='weather_ПРС-10'),
        types.InlineKeyboardButton('ПРС-11', callback_data='weather_ПРС-11'),
        types.InlineKeyboardButton('ПРС-12', callback_data='weather_ПРС-12'),
        types.InlineKeyboardButton('ПРС-13', callback_data='weather_ПРС-13'),
        types.InlineKeyboardButton('КС 5 - 7', callback_data='weather_КС-5-7'),
        types.InlineKeyboardButton('Утт и СТ', callback_data='weather_Утт-и-СТ'),
    ]
    weather_markup = types.InlineKeyboardMarkup()
    weather_markup.add(*weather_buttons)

    callback_message = bot.send_message(message.chat.id, 'Выберите объект:', reply_markup=weather_markup)

    # Создаем новое подключение к базе данных для текущего потока
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        # Создаем таблицу, если она еще не существует
        cursor.execute('CREATE TABLE IF NOT EXISTS weather_data(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, message TEXT, photo TEXT, data INTEGER)')
        # Сохраняем данные в базе данных
        cursor.execute("INSERT INTO weather_data (name, message, photo, data) VALUES (?, ?, ?, ?)",
                      ('Фото', message.text, message.photo[-1].file_id, message.date))

@bot.callback_query_handler(func=lambda call: call.data.startswith('weather_'))
def weather_action_callback(call):
    action = call.data.split('_')[1]

    if action in ['ПРС-10', 'ПРС-11', 'ПРС-12', 'ПРС-13', 'КС-5-7', 'Утт-и-СТ']:
        weather_text = f'Введите замечания по АПК {action}:'

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, '', show_alert=True)

        @bot.message_handler(content_types=['text'])
        def save_weather_data(message):
            # Создаем новое подключение к базе данных для текущего потока
            conn = get_db_connection()
            with conn:
                cursor = conn.cursor()
                # Сохраняем данные в базе данных

                cursor.execute("INSERT INTO weather_data (name, message, photo, data) VALUES (?, ?, ?, ?)",
                              (action, message.text, message.photo[-1].file_id if message.photo else '', message.date))
            bot.send_message(message.chat.id, 'Замечания сохранены!')

        bot.register_next_step_handler(call.message, save_weather_data)
        bot.send_message(call.message.chat.id, weather_text)

# Запускаем бота
bot.polling(non_stop=True)










4.76
#============================================================================================================
import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Создаем объект бота с токеном API
bot = telebot.TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')

@bot.message_handler(commands=['hellp', 'weather'])
def command_handler(message):
    if message.text == '/hellp':
        bot.send_message(message.chat.id, 'Приветствую вас!\n\nКоманды бота:\n\n/main - вернуться в главное меню\n/hellp - приветствие и помощь\n/weather - открыть сайт погоды\n\nДля запуска бота нажми на\n значёк скрепки, прикрепить фаил: photo'
                                          '\nили импортируй сюда фото\n из галерей своего устройства')
    elif message.text == '/weather':
        weather_link = 'https://yandex.ru/weather/?lat=63.71604156&lon=66.66759491&via=ssc'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)



#меню иконки commands
@bot.message_handler(commands=['start', 'main', 'hello'])
def main(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')

@bot.message_handler(commands=['hellp'])
def help(message):
    help_text = '''

#**Команды:**

#/weather - открыть погоду
#/main - вернуться в главное меню
#/hellp - вывести справку

'''
#bot.send_message(message.chat.id, help_text, parse_mode='html')


def save_object_name(chat_id, file_id, name, comment):
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()

        # Проверяем, существует ли таблица users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if cursor.fetchone() is None:
            # Таблицы нет, создаем ее
            cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT, name TEXT, comment TEXT)')
            connection.commit()

        # Сохраняем идентификатор фотографии, название объекта и комментарий в базе данных
        cursor.execute("INSERT INTO users (file_id, name, comment) VALUES (?, ?, ?)", (file_id, name, comment))
        connection.commit()

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, 'Введите название объекта:')
    bot.register_next_step_handler(message, handle_name, file_id)

def handle_name(message, file_id):
    name = message.text
    bot.send_message(message.chat.id, 'Введите комментарий к объекту:')
    bot.register_next_step_handler(message, handle_comment, file_id, name)

def handle_comment(message, file_id, name):
    comment = message.text
    save_object_name(message.chat.id, file_id, name, comment)
    bot.send_message(message.chat.id, 'Данные сохранены.')
    show_last_row(message.chat.id, 1)

def show_last_row(chat_id, page_num):
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()

        # Получаем общее количество строк в таблице
        cursor.execute("SELECT COUNT(*) FROM users")
        total_rows = cursor.fetchone()[0]

        # Получаем общее количество страниц
        total_pages = (total_rows - 1) // 1 + 1

        # Проверяем, находится ли запрашиваемая страница в допустимом диапазоне
        if page_num < 1 or page_num > total_pages:
            bot.send_message(chat_id, 'Неверный номер страницы.')
            return

        # Получаем строки из таблицы users с фильтрацией по столбцу name
        cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1 OFFSET ?;", ((page_num - 1) * 1,))
        row = cursor.fetchone()

        if not row:
            bot.send_message(chat_id, 'Нет сохраненных объектов.')
            return

        # Отправляем фото, используя его идентификатор из базы данных
        bot.send_photo(chat_id, row[1])

        message_text = f'Название объекта: {row[2]}\n'
        message_text += f'Комментарий: {row[3]}\n\n'

        # Отправляем сообщение с данными
        message_id = bot.send_message(chat_id, message_text).message_id

        # Создаем инлайн-клавиатуру с кнопками "Назад", "Страница" и "Вперед"
        markup = InlineKeyboardMarkup()
        if page_num > 1:
            markup.add(InlineKeyboardButton(text="Назад", callback_data=f"back:{page_num - 1}"))
        markup.add(InlineKeyboardButton(text=f"Страница {page_num}", callback_data=f"page:{page_num}"))
        if page_num < total_pages:
            markup.add(InlineKeyboardButton(text="Вперед", callback_data=f"forward:{page_num + 1}"))

        # Отправляем сообщение с кнопками
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("back:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("forward:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("page:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_rows = cursor.fetchone()[0]
        total_pages = (total_rows - 1) // 1 + 1

    if call.data.startswith("back:"):
        page_num = int(call.data.split(":")[1])
        if page_num > 1:
            show_last_row(call.message.chat.id, page_num, total_pages)
    elif call.data.startswith("forward:"):
        page_num = int(call.data.split(":")[1])
        if page_num < total_pages:
            show_last_row(call.message.chat.id, page_num, total_pages)
    elif call.data.startswith("page:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num, total_pages)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_rows = cursor.fetchone()[0]
        total_pages = (total_rows - 1) // 1 + 1

    if call.data.startswith("back:"):
        page_num = int(call.data.split(":")[1])
        if page_num > 1:
            show_last_row(call.message.chat.id, page_num, total_pages)
    elif call.data.startswith("forward:"):
        page_num = int(call.data.split(":")[1])
        if page_num < total_pages:
            show_last_row(call.message.chat.id, page_num, total_pages)
    elif call.data.startswith("page:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num, total_pages)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("back:"):
        page_num = int(call.data.split(":")[1])
        if page_num > 1:
            show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("forward:"):
        page_num = int(call.data.split(":")[1])
        total_pages = (total_rows - 1) // 1 + 1
        if page_num < total_pages:
            show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("page:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_rows = cursor.fetchone()[0]
        total_pages = (total_rows - 1) // 1 + 1

    if call.data.startswith("back:"):
        page_num = int(call.data.split(":")[1])
        if page_num > 1:
            show_last_row(call.message.chat.id, page_num, total_pages)
    elif call.data.startswith("forward:"):
        page_num = int(call.data.split(":")[1])
        if page_num < total_pages:
            show_last_row(call.message.chat.id, page_num, total_pages)
    elif call.data.startswith("page:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num, total_pages)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("back:"):
        page_num = int(call.data.split(":")[1])
        if page_num > 1:
            show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("forward:"):
        page_num = int(call.data.split(":")[1])
        total_pages = (total_rows - 1) // 1 + 1
        if page_num < total_pages:
            show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("page:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("back:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("forward:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("page:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("back:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)
    elif call.data.startswith("forward:"):
        page_num = int(call.data.split(":")[1])
        show_last_row(call.message.chat.id, page_num)
    elif call.data == "page":
        pass  # Обработка нажатия на кнопку "Страница"

# Запуск бота
bot.polling(none_stop=True)





3.52
#=============================================================================================
import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Создаем объект бота с токеном API
bot = telebot.TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')

def save_object_name(chat_id, file_id, name, comment):
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # Проверяем, существует ли таблица users
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if cursor.fetchone() is None:
        # Таблицы нет, создаем ее
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, file_id TEXT, name TEXT, comment TEXT)')
        connection.commit()

    # Сохраняем идентификатор фотографии, название объекта и комментарий в базе данных
    cursor.execute("INSERT INTO users (file_id, name, comment) VALUES (?, ?, ?)", (file_id, name, comment))
    connection.commit()

    # Закрываем курсор и соединение
    cursor.close()
    connection.close()

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, 'Введите название объекта:')
    bot.register_next_step_handler(message, handle_name, file_id)

def handle_name(message, file_id):
    name = message.text
    bot.send_message(message.chat.id, 'Введите комментарий к объекту:')
    bot.register_next_step_handler(message, handle_comment, file_id, name)

def handle_comment(message, file_id, name):
    comment = message.text
    save_object_name(message.chat.id, file_id, name, comment)
    bot.send_message(message.chat.id, 'Название объекта, комментарий и идентификатор фотографии сохранены.')
    show_last_row(message.chat.id, 1)

def show_last_row(chat_id, page_num):
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # Получаем общее количество строк в таблице
    cursor.execute("SELECT COUNT(*) FROM users")
    total_rows = cursor.fetchone()[0]

    # Получаем последнюю строку из таблицы users
    cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1 OFFSET ?", ((page_num - 1) * 1,))
    row = cursor.fetchone()

    # Проверяем, существует ли последняя строка
    if row is None:
        bot.send_message(chat_id, 'Нет сохраненных объектов.')
        return

    # Формируем и отправляем сообщение с данными
    message_text = ''
    # Отправляем фото, используя его идентификатор из базы данных
    bot.send_photo(chat_id, row[1])

    message_text += f'Название объекта: {row[2]}\n'
    message_text += f'Комментарий: {row[3]}\n\n'

    # Рассчитываем пройденные и оставшиеся сообщения
    passed_messages = page_num * 1
    remaining_messages = total_rows - passed_messages

    # Создаем инлайн-клавиатуру с кнопками "Назад", "Страница" и "Вперед"
    markup = InlineKeyboardMarkup()
    if page_num > 1:
        markup.add(InlineKeyboardButton(text="Назад", callback_data=f"back:{page_num - 1}"))
    markup.add(InlineKeyboardButton(text=f"Страница {page_num}", callback_data="page"))
    if remaining_messages > 0:
        markup.add(InlineKeyboardButton(text="Вперед", callback_data=f"forward:{page_num + 1}"))

    # Отправляем сообщение с кнопками
    bot.send_message(chat_id, message_text, reply_markup=markup)

    # Закрываем курсор и соединение
    cursor.close()
    connection.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("back"))
def back_button_handler(call):
    page_num = int(call.data.split(':')[1])
    show_last_row(call.message.chat.id, page_num)

@bot.callback_query_handler(func=lambda call: call.data.startswith("forward"))
def forward_button_handler(call):
    page_num = int(call.data.split(':')[1])
    show_last_row(call.message.chat.id, page_num)

@bot.callback_query_handler(func=lambda call: call.data == "page")
def page_button_handler(call):
    bot.answer_callback_query(call.id)

# Запускаем бота
bot.polling(none_stop=True)


#==============================================================
#2.17

import telebot
import sqlite3

bot = telebot.TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')
name = None


@bot.message_handler(content_types=['photo'])
def photo(message):
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), pass VARCHAR(50), file_id VARCHAR(50))')
    connection.commit()
    cursor.close()
    connection.close()

    bot.send_message(message.chat.id, 'Привет, как твои дела? Как тебя зовут?')
    bot.register_next_step_handler(message, get_name)  # Исправлено: передаем объект message, а не его chat.id




def get_photo(message):
    file_id = message.photo[-1].file_id
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    global name
    name = message.text
    bot.send_message(message.chat.id, 'Твой пароль:')
    bot.register_next_step_handler(message, get_password)  # Исправлено: передаем объект message, а не его chat.id


def get_password(message):
    password = message.text

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    cursor.execute("INSERT INTO users (name, password) VALUES (?, ?)", (name, password))
    connection.commit()
    cursor.close()
    connection.close()

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('Список желаний', callback_data='users'))
    bot.send_message(message.chat.id, 'Это твой лучший день!', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)  # Исправлено: используем правильный декоратор
def callback(call):
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    info = ''
    for el in users:
        info += f'Имя: {el[1]}, пароль: {el[2]}\n'

    cursor.close()
    connection.close()

    bot.send_message(call.message.chat.id, info)


bot.polling(none_stop=True)


'''
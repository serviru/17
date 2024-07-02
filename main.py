'''

#базовы код
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


@bot.message_handler(commands=['help', 'weather'])
def command_handler(message):
    """
    Приветствую вас!
    help - приветствие и помощь
    /weather - открыть сайт погоды

    Для запуска бота нажми на
    запуск или на команду старт в menu
    """
    if message.text == '/help':
        bot.send_message(message.chat.id, command_handler.__doc__)
    elif message.text == '/weather':
        weather_link = 'https://www.ventusky.com/ru/beloyarskiy'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)




# Словарь с доступными объектами
object_names = {
    'ПРС-10': 'ПРС-10',
    'ПРС-11': 'ПРС-11',
    'УРС-12': 'УРС-12',
    'ПРС-13': 'ПРС-13',
    'КС-5-7': 'КС 5 - 7',
    'Утт и Ст': 'Утт и Ст',
    'Другие обьекты': 'Другие обьекты'
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


#======================================================================================================



def show_object_selection(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    keyboard.add(*buttons)

    
    msg = bot.send_message(message.chat.id, "Выберите объект:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_selected_object)
    
#======================================================================================================
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
    #buttons.append(types.KeyboardButton("Все объекты"))
    buttons.append(types.KeyboardButton("Домой"))
    keyboard.add(*buttons)
    msg = bot.send_message(message.chat.id, "Выберите объект для просмотра:", reply_markup=keyboard)
    #bot.register_next_step_handler(msg, look_data)
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


#==========================================================================
#работаем над этим кодом




import telebot
import sqlite3
from telebot import types
from telebot.apihelper import ApiTelegramException
import time
from aiogram import Dispatcher
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler 
from telegram import ReplyKeyboardMarkup 







# Инициализация бота
bot = telebot.TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')
#bot = TeleBot('')


# создаёт клавиатуру edit_delete_keyboard

edit_delete_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        ["Редактировать", "Удалить"],
        ["Отмена"]
    ],
    resize_keyboard=True
)
#===========================================================================
'''
@bot.message_handler(commands=['help', 'weather'])
def command_handler(message):
    """
    Приветствую вас!
    help - приветствие и помощь
    /weather - открыть сайт погоды

    Для запуска бота нажми на
    запуск или на команду старт в menu
    """
    if message.text == '/help':
        bot.send_message(message.chat.id, command_handler.__doc__)
    elif message.text == '/weather':
        weather_link = 'https://www.ventusky.com/ru/beloyarskiy'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)
'''
#=============================================================================================================================================
# Другие функции обработки команд и сообщений
@bot.message_handler(commands=['help', 'start'])
def command_handler(message):
    if message.text == '/help':
        bot.send_message(message.chat.id, 'Приветствую вас!\n\nКоманды бота:\n\n/start - Активация бота\n/help - приветствие и помощь')
    elif message.text == '/start':
        start(message)
#========================================================================================================================================================

# Словарь с доступными объектами
object_names = {
    'ПРС-10': 'ПРС-10',
    'ПРС-11': 'ПРС-11',
    'УРС-12': 'УРС-12',
    'ПРС-13': 'ПРС-13',
    'KС-5-7': 'КС 5 - 7',
    'Утт и СТ': 'Утт и Ст',
    'Другие обьекты': 'Другие обьекты'

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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS completed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                user_id INTEGER,
                completed_at TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
     
                     
                        """)
        
'''
#=========================================================================================
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS completed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                user_id INTEGER,
                completed_at TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

'''        
#==================================================================================================
def add_user(username, chat_id):
       print(f"Attempting to add user: username={username}, chat_id={chat_id}")
       conn = get_db_connection()
       with conn:
           try:
               conn.execute("INSERT INTO users (username, chat_id) VALUES (?, ?)", (username, chat_id))
           except sqlite3.IntegrityError as e:
               print(f"SQLite IntegrityError: {e}")
               # Если пользователь уже существует, ничего не делаем
               pass



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

@bot.message_handler(commands=['start'])
def start(message):
    user = bot.get_chat(message.chat.id)
    user_id = get_user_id(message.chat.id)
    if not user_id:
        add_user(user.username, message.chat.id)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton("Добавить"),
        types.KeyboardButton("Просмотреть"),
        types.KeyboardButton("Выполнено"),
        types.KeyboardButton("Отмена")
    )
    return keyboard

@bot.message_handler(func=lambda message: message.text in ['Добавить', 'Просмотреть', 'Выполнено', 'Отмена'])
def handle_menu_option(message):
    if message.text == 'Добавить':
        show_object_selection(message)
    elif message.text == 'Просмотреть':
        show_menu(message)
    elif message.text == 'Выполнено':
        show_menu_completed(message)
    elif message.text == 'Отмена':
        bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())


def mark_as_completed(chat_id, item_id):
    user_id = get_user_id(chat_id)
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO completed (item_id, user_id, completed_at) VALUES (?, ?, DATE('now'))", (item_id, user_id))
        
    # Отправляем сообщение пользователю
    bot.send_message(chat_id, "Задача отмечена как выполненная.")

def show_completed_tasks(chat_id):
    user_id = get_user_id(chat_id)
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT items.object_name, completed.completed_at "
                      "FROM completed "
                      "JOIN items ON completed.item_id = items.id "
                      "WHERE completed.user_id = ? "
                      "ORDER BY completed.completed_at DESC", (user_id,))
        rows = cursor.fetchall()
        
        if rows:
            message = "Выполненные задачи:\n\n"
            for row in rows:
                message += f"- {row[0]} (выполнено {row[1]})\n"
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            keyboard.add(types.KeyboardButton("Назад"))
            bot.send_message(chat_id, message, reply_markup=keyboard)
        else:
            bot.send_message(chat_id, "У вас пока нет выполненных задач.", reply_markup=get_main_menu_keyboard())
#====================================================================================================================================================================================================
#работа с кнопкой просмотреть
def show_menu(message):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT object_name FROM items")
    object_names = [row[0] for row in c.fetchall()]

    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names]
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])

    markup.add(types.KeyboardButton('Меню'))

    bot.send_message(chat_id=message.chat.id, text='Выберите, что вы хотите просмотреть:', reply_markup=markup)

#===================================================================================================================================================================================================
#работа с кнопкой выполнено
def show_menu_completed(message):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT object_name FROM items")
    object_names = [row[0] for row in c.fetchall()]

    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names]
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])

    markup.add(types.KeyboardButton('Меню'))

    bot.send_message(chat_id=message.chat.id, text='Выберите, что вы хотите редактировать:', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def handle_menu_options(message):
        if message.text in object_names:
            # Обработка выбора конкретного объекта
            show_object_details(message, message.text)
        elif message.text == 'Меню':
            start(message)

        else:
            bot.send_message(chat_id=message.chat.id, text='Неверный выбор. Попробуйте еще раз.')
'''
def show_all_objects(message):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT object_name, message, photos.file_id FROM items "
              "LEFT JOIN photos ON items.photo_id = photos.id")
    rows = c.fetchall()
    for row in rows:
        if row[2]:
            bot.send_photo(chat_id=message.chat.id, photo=row[2],
                           caption=f"Объект: {row[0]}\nСообщение: {row[1]}")
        else:
            bot.send_message(chat_id=message.chat.id, text=f"Объект: {row[0]}\nСообщение: {row[1]}")
'''

def show_object_details(message, object_name, page=1):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT items.id, object_name, message, photos.file_id "
              "FROM items "
              "LEFT JOIN photos ON items.photo_id = photos.id "
              "WHERE object_name = ? "
              "LIMIT 1 OFFSET ?", (object_name, (page - 1) * 1))
    row = c.fetchone()
    if row:
        if row[3]:
            bot.send_photo(chat_id=message.chat.id, photo=row[3],
                           caption=f"Объект: {row[1]}\nСообщение: {row[2]}")
        else:
            bot.send_message(chat_id=message.chat.id, text=f"Объект: {row[1]}\nСообщение: {row[2]}")

        c.execute("SELECT COUNT(*) FROM items WHERE object_name = ?", (object_name,))
        total_count = c.fetchone()[0]
        current_page = page

        # Вычисляем количество страниц
        objects_per_page = 1
        total_pages = (total_count + objects_per_page - 1) // objects_per_page

        


        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = []
        if current_page > 1:
            buttons.append(types.InlineKeyboardButton("Предыдущий", callback_data=f"prev_{object_name}_{current_page-1}"))
        #buttons.append(types.InlineKeyboardButton("Выбрать", callback_data=f"show_menu{row[0]}"))
        if current_page < total_pages:
            buttons.append(types.InlineKeyboardButton("Следующий", callback_data=f"next_{object_name}_{current_page+1}"))
        buttons.append(types.InlineKeyboardButton("Назад", callback_data="back"))
        markup.add(*buttons)


        
        bot.send_message(chat_id=message.chat.id, text=f"Страница {current_page} из {total_pages}", reply_markup=markup)
    else:
        bot.send_message(chat_id=message.chat.id, text='Объект не найден.')


        
def get_object_details(object_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT object_name, message, photos.file_id "
                      "FROM items "
                      "LEFT JOIN photos ON items.photo_id = photos.id "
                      "WHERE items.id = ?", (object_id,))
        row = cursor.fetchone()
        if row:
            return {
                "object_name": row[0],
                "message": row[1],
                "file_id": row[2]
            }
        else:
            return None

'''

def edit_delete_keyboard():
    keyboard = [[InlineKeyboardButton("Редактировать", callback_data="edit"),
                 InlineKeyboardButton("Удалить", callback_data="delete")]]
    return InlineKeyboardMarkup(keyboard)
'''
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("prev_"):
        _, object_name, page = call.data.split("_")
        show_object_details(call.message, object_name, int(page))
    elif call.data.startswith("next_"):
        _, object_name, page = call.data.split("_")
        show_object_details(call.message, object_name, int(page))
    #elif call.data.startswith("select_"):
        #_, object_id = call.data.split("_")
        #show_object_details_with_actions(call.message.chat.id, object_id)
    elif call.data == "done":
        # Обработка кнопки "Выполнено"
        pass
    elif call.data == "back":
        show_menu(call.message)
    bot.answer_callback_query(call.id)

def show_object_details_with_actions(chat_id, object_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT items.object_name, items.message, photos.file_id, items.user_id "
                      "FROM items "
                      "LEFT JOIN photos ON items.photo_id = photos.id "
                      "WHERE items.id = ?", (object_id,))
        row = cursor.fetchone()
        if row:
            message_text = f"Объект: {row[0]}\nСообщение: {row[1]}"
            if row[2]:
                # Если есть фото, отправляем его
                bot.send_photo(chat_id=chat_id, photo=row[2], caption=message_text)
            else:
                # Если нет фото, отправляем только текст
                bot.send_message(chat_id=chat_id, text=message_text)

            # Получаем идентификатор пользователя, который создал объект
            user_id = row[3]

            # Формируем клавиатуру с кнопками
            add_photo_button = InlineKeyboardButton("Добавить фото", callback_data=f"add_photo_{object_id}")
            edit_message_button = InlineKeyboardButton("Изменить сообщение", callback_data=f"edit_message_{object_id}")
            menu_button = InlineKeyboardButton("Меню", callback_data="back")
            keyboard = InlineKeyboardMarkup([[add_photo_button, edit_message_button], [menu_button]])
            bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=keyboard)
        else:
            # Если объект не найден, отправляем сообщение об ошибке
            bot.send_message(chat_id=chat_id, text="Объект не найден.")

def handle_add_photo(chat_id, object_id, user_id):
    # Проверяем, является ли пользователь владельцем объекта
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM items WHERE id = ?", (object_id,))
        owner_id = cursor.fetchone()[0]
        if owner_id != user_id:
            bot.send_message(chat_id=chat_id, text="У вас нет прав на добавление фото к этому объекту.")
            return

    # Ожидаем отправки фото от пользователя
    msg = bot.send_message(chat_id=chat_id, text="Отправьте фото, которое вы хотите добавить к этому объекту.")
'''
@bot.message_handler(content_types=['photo'], chat_id=chat_id)
def add_photo(message):
        # Получаем файл-идентификатор отправленной фото
        file_id = message.photo[-1].file_id

        # Сохраняем файл-идентификатор в таблице фотографий
        conn = get_db_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO photos (file_id) VALUES (?)", (file_id,))
            photo_id = cursor.lastrowid

        # Обновляем запись объекта, добавляя новое фото
        with conn:
            cursor.execute("UPDATE items SET photo_id = ? WHERE id = ?", (photo_id, object_id))

        bot.send_message(chat_id=chat_id, text="Фото успешно добавлено к объекту.")

        bot.register_next_step_handler(message, add_photo)
'''
def handle_edit_message(chat_id, object_id, user_id):
    # Проверяем, является ли пользователь владельцем объекта
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM items WHERE id = ?", (object_id,))
        owner_id = cursor.fetchone()[0]
        if owner_id != user_id:
            bot.send_message(chat_id=chat_id, text="У вас нет прав на изменение сообщения этого объекта.")
            return

    # Ожидаем отправки нового сообщения от пользователя
    msg = bot.send_message(chat_id=chat_id, text="Отправьте новое сообщение для этого объекта.")

    @bot.message_handler(content_types=['text'], chat_id=chat_id)
    def update_message(message):
        new_message = message.text

        # Обновляем запись объекта, изменяя сообщение
        with conn:
            cursor.execute("UPDATE items SET message = ? WHERE id = ?", (new_message, object_id))

        bot.send_message(chat_id=chat_id, text="Сообщение успешно изменено.")

    bot.register_next_step_handler(msg, update_message)

def show_object_details_with_actions(chat_id, object_id):
    # Получаем детали объекта
    object_details = get_object_details(object_id)
    if object_details:
        # Формируем сообщение с деталями объекта
        message_text = f"Объект: {object_details['object_name']}\nСообщение: {object_details['message']}"
        if object_details['file_id']:
            # Если есть фото, отправляем его
            bot.send_photo(chat_id=chat_id, photo=object_details['file_id'], caption=message_text)
        else:
            # Если нет фото, отправляем только текст
            bot.send_message(chat_id=chat_id, text=message_text)

        # Формируем клавиатуру с кнопками
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Добавить фото", callback_data=f"add_photo_{object_id}")],
            [InlineKeyboardButton("Изменить сообщение", callback_data=f"edit_message_{object_id}")],
            [InlineKeyboardButton("Меню", callback_data="back")]
        ])
        bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=keyboard)
    else:
        # Если объект не найден, отправляем сообщение об ошибке
        bot.send_message(chat_id=chat_id, text="Объект не найден.")


    bot.message_handler(state='editing', func=lambda message: message.text == "Отмена")

def handle_edit_menu_cancel(message):
    # Возвращаем пользователя в главное меню
    start(message)

def get_objects_for_editing():
    # Возвращаем ключи словаря object_names
    return list(object_names.keys())

def show_main_menu(update, context):
    # Создание клавиатуры с основными опциями
    keyboard = get_main_menu_keyboard()
    context.bot.send_message(chat_id=update.effective_chat.id, text="Главное меню", reply_markup=keyboard)
    bot.send_message(chat_id=message.chat.id, text="Меню редактирования") # type: ignore

def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

def get_unique_object_names():
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT object_name FROM items")
        return [row[0] for row in cursor.fetchall()]

def show_object_selection(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    buttons.append(types.KeyboardButton("Меню"))
    keyboard.add(*buttons)

    msg = bot.send_message(message.chat.id, "Выберите объект:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_selected_object)

@bot.message_handler(func=lambda message: message.text == "Отмена")
def handle_object_selection_cancel(message):
    # Возвращаем пользователя в главное меню
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

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
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(name, callback_data=name) for name in object_names.values()]
    buttons.append(types.InlineKeyboardButton("Отмена", callback_data="cancel"))
    keyboard.add(*buttons)
    bot.send_message(message.chat.id, "Выберите объект для просмотра:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def look_data(call):
    if call.data == "cancel":
        start(call.message)
    else:
        user_id = get_user_id(call.message.chat.id)
        if user_id:
            for key, value in object_names.items():
                if value == call.data:
                    object_name = key
                    break
            filter_data_by_object(call.message, object_name)
        else:
            bot.send_message(call.message.chat.id, "Вы не зарегистрированы в системе. Пожалуйста, используйте команду /start.")
    bot.answer_callback_query(call.id)

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

def main() -> None:
    """
    Главная функция, запускающая бота.
    """
    updater = updater(token="6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU")
    dispatcher: Dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    updater.start_polling()

if __name__ == '__main__':
    create_tables()
    print("Запуск бота...")
    while True:
        try:
            bot.polling(non_stop=True)
        except ApiTelegramException as e:
            if e.error_code == 409:
                print("Бот уже работает, перезапускаем...")
                bot.stop_polling()
                bot.polling(non_stop=True)
            else:
                raise e

'''
=======================================================================================================================================================================


from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import sqlite3


def start(update, context):
    # Создаем инлайн-клавиатуру с кнопками в ряд по две, адаптируясь к ширине экрана
    keyboard = [
        [InlineKeyboardButton("Изменить", callback_data='edit', resize_keyboard=True, width=1),
         InlineKeyboardButton("Удалить", callback_data='delete', resize_keyboard=True, width=1)],
        [InlineKeyboardButton("Отмена", callback_data='cancel', resize_keyboard=True, width=1)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True)

    # Отправляем сообщение с инлайн-клавиатурой
    context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите действие:", reply_markup=reply_markup)

    # Регистрируем обработчик для обработки нажатий на кнопки
    context.dispatcher.add_handler(CallbackQueryHandler(button_click))


def button_click(update, context):
    query = update.callback_query
    query.answer()  # Удаляем индикатор загрузки

    if query.data == 'delete':
        # Создаем новое соединение с базой данных для этого потока
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Извлекаем все данные из таблицы items и связанные фото из таблицы photos
        c.execute("SELECT i.object_name, p.file_id, i.message FROM items i LEFT JOIN photos p ON i.photo_id = p.id")
        results = c.fetchall()

        if results:
            # Устанавливаем индекс начального сообщения
            context.user_data['current_index'] = 0

            # Отправляем первое сообщение
            send_message(update, context, results, 0)
        else:
            context.bot.send_message(chat_id=query.message.chat_id, text="Нет сохраненных объектов.")

        # Закрываем соединение с базой данных
        conn.close()
    elif query.data == 'next':
        # Получаем список результатов и текущий индекс
        results = context.user_data.get('results', [])
        current_index = context.user_data.get('current_index', 0)

        # Проверяем, есть ли следующее сообщение
        if current_index + 1 < len(results):
            # Отправляем следующее сообщение
            send_message(update, context, results, current_index + 1)
            context.user_data['current_index'] = current_index + 1
    elif query.data == 'prev':
        # Получаем список результатов и текущий индекс
        results = context.user_data.get('results', [])
        current_index = context.user_data.get('current_index', 0)

        # Проверяем, есть ли предыдущее сообщение
        if current_index > 0:
            # Отправляем предыдущее сообщение
            send_message(update, context, results, current_index - 1)
            context.user_data['current_index'] = current_index - 1
    elif query.data == 'edit':
        # Вызываем функцию show_message_actions
        show_message_actions(update, context)
    elif query.data == 'save':
        # Вызываем функцию show_message_actions
        show_message_actions(update, context)
    elif query.data == 'cancel':
        # Вызываем функцию show_message_actions
        show_message_actions(update, context)


def send_message(update, context, results, index):
    object_name, file_id, message = results[index]

    # Создаем инлайн-клавиатуру с кнопками "Предыдущий" и "Следующий"
    keyboard = [
        [InlineKeyboardButton("Предыдущий", callback_data='prev', resize_keyboard=True, width=1),

         InlineKeyboardButton("Следующий", callback_data='next', resize_keyboard=True, width=1)],
        [InlineKeyboardButton("Выбрать", callback_data='edit', resize_keyboard=True, width=1)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True)

    # Отправляем сообщение с фото или текстом
    if file_id:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=file_id, caption=f"{object_name}\n{message}",
                               reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"{object_name}\n{message}",
                                 reply_markup=reply_markup)

    # Сохраняем список результатов в контекст пользователя
    context.user_data['results'] = results

    # Сохраняем индекс текущего сообщения в контекст пользователя
    context.user_data['current_index'] = index


def show_message_actions(update, context):
    # Получаем индекс текущего сообщения из контекста пользователя
    current_index = context.user_data.get('current_index', 0)
    results = context.user_data.get('results', [])

    # Создаем инлайн-клавиатуру с кнопками "Изменить", "Сохранить" и "Назад"
    keyboard = [
        [InlineKeyboardButton("Изменить", callback_data='edit', resize_keyboard=True, width=1),
         InlineKeyboardButton("Сохранить", callback_data='save', resize_keyboard=True, width=1)],
        [InlineKeyboardButton("Назад", callback_data='cancel', resize_keyboard=True, width=1)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True)

    # Отправляем сообщение с фото или текстом и инлайн-клавиатурой
    object_name, file_id, message = results[current_index]
    if file_id:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=file_id, caption=f"{object_name}\n{message}",
                               reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"{object_name}\n{message}",
                                 reply_markup=reply_markup)


def main():
    updater = Updater(token='6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU', use_context=True)
    dispatcher = updater.dispatcher

    # Регистрируем обработчики команд и callback-ов
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_click))
    dispatcher.add_handler(CallbackQueryHandler(show_message_actions, pattern='edit|save|cancel'))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU
#=============================================================================================================
#код не код нужна тборадотка
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import sqlite3
import time

# Словарь с доступными объектами
object_names = {
    'PRS-10': 'ПРС-10',
    'PRS-11': 'ПРС-11',
    'UPRS-12': 'УРС-12',
    'PRS-13': 'ПРС-13',
    'KS-5-7': 'КС 5 - 7',
    'UTT-and-ST': 'Утт и Ст'
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

# Основная функция обработки обновлений
def main():
    updater = Updater(token='6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU', use_context=True)
    dispatcher = updater.dispatcher

    # Создание таблиц в базе данных
    create_tables()

    # Регистрация обработчиков
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('hellp', command_handler))
    dispatcher.add_handler(CommandHandler('weather', command_handler))
    dispatcher.add_handler(CommandHandler('main', command_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_menu_option))

    dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))

    updater.start_polling()
    updater.idle()

# Обработчик команды /start
def start(update, context):
    user = update.effective_chat
    user_id = get_user_id(user.id)
    if not user_id:
        add_user(user.username, user.id)
    context.bot.send_message(chat_id=user.id, text="Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

def get_main_menu_keyboard():
    keyboard = [[KeyboardButton("Добавить")],
                [KeyboardButton("Просмотреть")],
                [KeyboardButton("Отмена")]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return reply_markup

def handle_menu_option(update, context):
    text = update.message.text
    if text == 'Добавить':
        show_object_selection(update, context)
    elif text == 'Просмотреть':
        show_look_menu(update, context)
    elif text == 'Отмена':
        start(update, context)

def show_look_menu(update, context):
    show_pagination_menu(update, context, ["Элемент 1", "Элемент 2", "Элемент 3", "Элемент 4", "Элемент 5", "Элемент 6", "Элемент 7", "Элемент 8", "Элемент 9", "Элемент 10"])

def show_pagination_menu(update, context, items, page=1, per_page=5):
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page
    start_index = (page - 1) * per_page
    end_index = min(start_index + per_page, total_items)

    keyboard = [[
        InlineKeyboardButton("◀️ Назад", callback_data=f"page:{page - 1}"),
        InlineKeyboardButton(f"{page}/{total_pages}", callback_data="dummy"),
        InlineKeyboardButton("Вперед ▶️", callback_data=f"page:{page + 1}")
    ]]
    if page > 1:
        keyboard[0].insert(0, InlineKeyboardButton("Отмена", callback_data="cancel"))
    if page < total_pages:
        keyboard[0].append(InlineKeyboardButton("Отмена", callback_data="cancel"))

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "\n".join([f"{i + 1}. {item}" for i, item in enumerate(items[start_index:end_index])])
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, reply_markup=reply_markup)

def handle_callback_query(update, context):
    call = update.callback_query
    data = call.data
    if data.startswith("page:"):
        page = int(data.split(":")[1])
        if page >= 1:
            show_pagination_menu(update, context, ["Элемент 1", "Элемент 2", "Элемент 3", "Элемент 4", "Элемент 5", "Элемент 6", "Элемент 7", "Элемент 8", "Элемент 9", "Элемент 10"], page=page)
    elif data == "cancel":
        show_main_menu(update, context)
    call.answer()

def show_object_selection(update, context):
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons = [KeyboardButton(name) for name in object_names.values()]
    keyboard.add(*buttons)

    msg = context.bot.send_message(update.effective_chat.id, "Выберите объект:", reply_markup=keyboard)
    context.dispatcher.run_async(process_selected_object, context, msg)

def process_selected_object(context, msg):
    update = context.update
    selected_object = update.message.text
    for key, value in object_names.items():
        if value == selected_object:
            object_name = key
            break
    msg = context.bot.send_message(update.effective_chat.id, "Введите описание:")
    context.dispatcher.run_async(process_message, context, msg, object_name)

def process_message(context, msg, object_name):
    update = context.update
    message_text = update.message.text
    msg = context.bot.send_message(update.effective_chat.id, "Отправьте фото объекта:")

    context.dispatcher.run_async(process_photo, context, msg, object_name, message_text)

def process_photo(context, msg, object_name, message_text):
    update = context.update
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        photo_id = add_photo(file_id)
        user_id = get_user_id(update.effective_chat.id)
        add_item(object_name, photo_id, message_text, user_id)
        context.bot.reply_to(update.message, "Данные сохранены.")
    else:
        context.bot.reply_to(update.message, "Вы не отправили фото.")

def show_main_menu(update, context):
    keyboard = [[KeyboardButton("Добавить")],
                [KeyboardButton("Просмотреть")],
                [KeyboardButton("Отмена")]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите действие:", reply_markup=reply_markup)

def get_user_id(chat_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE chat_id = ?", (chat_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None

def command_handler(update, context):
    if update.message.text == '/hellp':
        context.bot.send_message(update.effective_chat.id, 'Приветствую вас!\n\nКоманды бота:\n\n/main - вернуться в главное меню\n/hellp - приветствие и помощь\n/weather - открыть сайт погоды\n\nДля запуска бота нажми на\n значёк скрепки, прикрепить фаил: photo'
                                          '\nили импортируй сюда фото\n из галерей своего устройства')
    elif update.message.text == '/weather':
        weather_link = 'https://yandex.ru/weather/?lat=63.71604156&lon=66.66759491&via=ssc'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        context.bot.send_message(update.effective_chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)
    elif update.message.text == '/main':
        start(update, context)

if __name__ == '__main__':
    create_tables()
    print("Запуск бота...")
    while True:
        try:
            main()
        except Exception as e:
            print(f"Ошибка при запуске бота: {e}")
            time.sleep(10)

'''



'''

#=====================================================================================================================

#ошибки в удалении и выводе сообщений пользователей
 
import os
import sqlite3
from telebot import TeleBot, types
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

import logging


# Инициализация бота
bot = TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')

@bot.message_handler(commands=['help', 'weather'])
def command_handler(message):
    """
    Приветствую вас!
    help - приветствие и помощь
    /weather - открыть сайт погоды

    Для запуска бота нажми на
    запуск или на команду старт в menu
    """
    if message.text == '/help':
        bot.send_message(message.chat.id, command_handler.__doc__)
    elif message.text == '/weather':
        weather_link = 'https://yandex.ru/weather/?lat=63.71604156&lon=66.66759491&via=ssc'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)




# Словарь с доступными объектами
object_names = {
    'ПРС-10': 'ПРС-10',
    'ПРС-11': 'ПРС-11',
    'УРС-12': 'УРС-12',
    'ПРС-13': 'ПРС-13',
    'КС-5-7': 'КС 5 - 7',
    'Утт и Ст': 'Утт и Ст'
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
            raise

def get_user_id(chat_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE chat_id = ?", (chat_id,))
        user = cursor.fetchone()
        return user[0] if user else None

def process_new_message(message, item_id, object_name):
    if object_name == "item":
        new_message = message.text
        update_item(item_id, new_message)
        bot.reply_to(message, "Сообщение было обновлено.")
    else:
        new_photo_id = get_photo_by_id(item_id)
        if message.photo:
            file_id = message.photo[-1].file_id
            update_item(item_id, None, file_id)
            bot.reply_to(message, "Фото было обновлено.")
        else:
            bot.reply_to(message, "Пожалуйста, отправьте фото.")


def update_message(message_id, new_message):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE items SET message = ? WHERE id = ?", (new_message, message_id))

def update_item(item_id, new_message, new_file_id=None):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        if new_file_id:
            cursor.execute("UPDATE items SET message = ?, file_id = ? WHERE id = ?", (new_message, new_file_id, item_id))
        else:
            cursor.execute("UPDATE items SET message = ? WHERE id = ?", (new_message, item_id))
        conn.commit()




def delete_item(item_id):
    conn = get_db_connection()
    with conn:

        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))

        # Обработчики команд

def get_message_by_id(item_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

def get_object_name_by_id(item_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT object_name FROM items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None




def update_message_in_db(message_id, new_text):
    try:
        # Подключение к базе данных
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Обновление текста сообщения
        cursor.execute("UPDATE messages SET text = ? WHERE id = ?", (new_text, message_id))
        conn.commit()

        # Закрытие соединения
        conn.close()
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении сообщения: {e}")
        raise



def update_photo_in_db(photo_id, new_photo):
    try:
        # Подключение к базе данных
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Обновление данных фотографии
        cursor.execute("UPDATE photos SET data = ? WHERE id = ?", (new_photo, photo_id))
        conn.commit()

        # Закрытие соединения
        conn.close()
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении фотографии: {e}")
        raise e


def get_photo_by_id(photo_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_id FROM photos WHERE id = ?", (photo_id,))
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        else:
            return None




@bot.message_handler(commands=['start'])
def start(message):
    user = bot.get_chat(message.chat.id)
    user_id = get_user_id(message.chat.id)
    if not user_id:
        add_user(user.username, message.chat.id)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in
               ['Добавить', 'Просмотреть', 'Редактировать/Удалить', 'Отмена']]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(
    func=lambda message: message.text in ['Добавить', 'Просмотреть', 'Редактировать/Удалить', 'Отмена'])
def handle_menu_option(message):
    if message.text == 'Добавить':
        show_object_selection(message)
    elif message.text == 'Просмотреть':
        show_look_menu(message)
    elif message.text == 'Редактировать/Удалить':
        show_edit_delete_menu(message)
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
        home_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_home = types.KeyboardButton("Домой")
        home_keyboard.add(button_home)

        # Отправка сообщения с клавиатурой
        bot.reply_to(message, "Данные сохранены.", reply_markup=home_keyboard)

        # Регистрация обработчика для кнопки "Домой"
        bot.register_next_step_handler(message, start)
    else:
        bot.reply_to(message, "Вы не отправили фото.")

def show_look_menu(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    buttons.append(types.KeyboardButton("Все объекты"))
    buttons.append(types.KeyboardButton("Домой"))
    keyboard.add(*buttons)
    msg = bot.send_message(message.chat.id, "Выберите объект для просмотра:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, look_data)
    bot.register_next_step_handler(msg, start)

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
        cursor.execute("SELECT items.message, photos.file_id "
                      "FROM items "
                      "INNER JOIN photos ON items.photo_id = photos.id "
                      "WHERE items.object_name = ? "
                      "ORDER BY items.id DESC",
                      (object_name,))
        data = cursor.fetchall()

    if data:
        for message_text, file_id in data:
            bot.send_photo(message.chat.id, file_id, caption=message_text)
    else:
        bot.send_message(message.chat.id, f"Нет данных для объекта {object_name}.")

def filter_data_by_user(message, user_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT items.object_name, items.message, photos.file_id "
                      "FROM items "
                      "INNER JOIN photos ON items.photo_id = photos.id "
                      "WHERE items.user_id = ? "
                      "ORDER BY items.id DESC",
                      (user_id,))
        data = cursor.fetchall()

    if data:
        for object_name, message_text, file_id in data:
            bot.send_photo(message.chat.id, file_id, caption=f"{object_name}: {message_text}")
    else:
        bot.send_message(message.chat.id, "У вас нет сохраненных данных.")


# Добавьте обработчик нажатия на объект в режиме редактирования
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def handle_edit_selection(call):
    # Извлекаем item_id, object_name и user_id из callback_data
    item_id = int(call.data.split("_")[1])
    object_name = call.data.split("_")[2]
    user_id = call.from_user.id

    # Вызываем process_edit_delete_selection() с нужными аргументами
    process_edit_delete_selection(item_id, object_name, user_id)

    # Обновляем сообщение пользователю
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Объект был обновлен.")


def show_edit_delete_menu(message, page=1, items_per_page=1):
    # Получаем идентификатор пользователя
    user_id = get_user_id(message.chat.id)
    if not user_id:
        # Если пользователь не зарегистрирован, отправляем сообщение
        bot.send_message(message.chat.id, "Вы не зарегистрированы в системе. Пожалуйста, используйте команду /start.")
        return

    # Подключаемся к базе данных
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        # Получаем все записи пользователя
        cursor.execute("SELECT id, object_name, message, photo_id FROM items WHERE user_id = ? ORDER BY id LIMIT ? OFFSET ?", (user_id, items_per_page, (page - 1) * items_per_page))
        items = cursor.fetchall()

    if not items:
        # Если нет записей, отправляем сообщение
        bot.send_message(message.chat.id, "У вас нет сохраненных сообщений или фотографий.")
        return

    # Перебираем записи и выводим их по одному
    for item in items:
        item_id, object_name, message_text, photo_id = item
        if object_name == "item":
            # Выводим сообщение
            bot.send_message(message.chat.id, message_text)
        elif object_name == "photo":
            # Выводим фото
            try:
                file_info = bot.get_file(photo_id)
                bot.send_photo(message.chat.id, file_info.file_id, caption=f"Фото ID: {item_id}")
            except Exception as e:
                bot.send_message(message.chat.id, f"Не удалось отобразить фото ID: {item_id}. Ошибка: {e}")

    # Создаем клавиатуру с кнопками для навигации и редактирования/удаления
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if page > 1:
        keyboard.add(types.InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"page_{page-1}"))
    if len(items) == items_per_page:
        keyboard.add(types.InlineKeyboardButton("Следующая ➡️", callback_data=f"page_{page+1}"))
    buttons = [types.InlineKeyboardButton(f"{item[0]} - {item[1]} - Редактировать", callback_data=f"edit_{item[0]}_{item[1]}") for item in items]
    buttons.extend([types.InlineKeyboardButton(f"{item[0]} - {item[1]} - Удалить", callback_data=f"delete_{item[0]}_{item[1]}") for item in items])
    keyboard.add(*buttons)
    bot.send_message(message.chat.id, "Выберите сообщение или фото для редактирования или удаления:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def handle_delete(call):
    item_id, object_name = call.data.split("_")[1:]
    # Подключаемся к базе данных
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        # Удаляем запись из базы данных
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    # Отправляем сообщение об удалении
    bot.send_message(call.message.chat.id, f"Запись с ID {item_id} была удалена.")
    # Обновляем меню с оставшимися записями
    show_edit_delete_menu(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def handle_page_navigation(call):
    page = int(call.data.split("_")[1])
    show_edit_delete_menu(call.message, page)
    bot.answer_callback_query(call.id)



@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_") or call.data.startswith("delete_"))
def handle_edit_delete_selection(call):
    # Обрабатываем выбор пользователя
    action, item_id, object_name = call.data.split("_")
    item_id = int(item_id)
    user_id = call.from_user.id

    if action == "edit":
        # Редактируем выбранный элемент
        process_edit_selection(item_id, object_name, user_id)
    elif action == "delete":
        # Удаляем выбранный элемент
        process_delete_selection(item_id, object_name, user_id)

    # Завершаем обработку callback-запроса
    bot.answer_callback_query(call.id)

def process_edit_selection(item_id, object_name, user_id):
    if object_name == "item":
        # Редактирование сообщения
        message_text = get_message_by_id(item_id)
        if message_text:
            msg = bot.send_message(user_id, f"Введите новый текст сообщения (текущий: {message_text})")
            bot.register_next_step_handler(msg, update_message, item_id, message_text)
    elif object_name == "photo":
        # Редактирование фото
        photo_data = get_photo_by_id(item_id)
        if photo_data:
            msg = bot.send_message(user_id, "Пожалуйста, отправьте новое фото")
            bot.register_next_step_handler(msg, update_photo, item_id, photo_data)
    else:
        # Некорректный тип объекта
        bot.send_message(user_id, "Некорректный тип объекта для редактирования")

def process_edit_delete_selection(item_id, object_name, user_id, text=None, photo_data=None):
    if object_name == "item":
        process_edit_selection(item_id, object_name, user_id, text)
    elif object_name == "photo":
        process_edit_selection(item_id, object_name, user_id, photo_data)


def process_delete_selection(item_id, object_name, user_id):
    if object_name == "item":
        # Удаление сообщения
        delete_item(item_id)
        bot.send_message(user_id, "Сообщение было удалено.")
    else:
        # Удаление фото
        delete_item(item_id)
        bot.send_message(user_id, "Фото было удалено.")


def update_message(new_text, item_id, object_name):
    try:
        # Обновить сообщение в базе данных
        update_message_in_db(item_id, new_text)

        # Вернуть обновленное сообщение
        updated_message = get_message_by_id(item_id)
        return updated_message

    except Exception as e:
        # Обработка ошибок
        print(f"Ошибка при обновлении сообщения: {e}")
        return None


def update_photo(new_photo, item_id, object_name):
    try:
        # Обновить фото в базе данных
        update_photo_in_db(item_id, new_photo)

        # Вернуть обновленное фото
        updated_photo = get_photo_by_id(item_id)
        return updated_photo

    except Exception as e:
        # Обработка ошибок
        print(f"Ошибка при обновлении фото: {e}")
        return None


bot.polling()



#===========================================================================
import os
import sqlite3
from telebot import TeleBot, types
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

import logging


# Инициализация бота
bot = TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')

@bot.message_handler(commands=['help', 'weather'])
def command_handler(message):
    """
    Приветствую вас!
    help - приветствие и помощь
    /weather - открыть сайт погоды

    Для запуска бота нажми на
    запуск или на команду старт в menu
    """
    if message.text == '/help':
        bot.send_message(message.chat.id, command_handler.__doc__)
    elif message.text == '/weather':
        weather_link = 'https://yandex.ru/weather/?lat=63.71604156&lon=66.66759491&via=ssc'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)




# Словарь с доступными объектами
object_names = {
    'ПРС-10': 'ПРС-10',
    'ПРС-11': 'ПРС-11',
    'УРС-12': 'УРС-12',
    'ПРС-13': 'ПРС-13',
    'КС-5-7': 'КС 5 - 7',
    'Утт и Ст': 'Утт и Ст'
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
            raise

def get_user_id(chat_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE chat_id = ?", (chat_id,))
        user = cursor.fetchone()
        return user[0] if user else None

def process_new_message(message, item_id, object_name):
    if object_name == "item":
        new_message = message.text
        update_item(item_id, new_message)
        bot.reply_to(message, "Сообщение было обновлено.")
    else:
        new_photo_id = get_photo_by_id(item_id)
        if message.photo:
            file_id = message.photo[-1].file_id
            update_item(item_id, None, file_id)
            bot.reply_to(message, "Фото было обновлено.")
        else:
            bot.reply_to(message, "Пожалуйста, отправьте фото.")


def update_message(message_id, new_message):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE items SET message = ? WHERE id = ?", (new_message, message_id))

def update_item(item_id, new_message, new_file_id=None):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        if new_file_id:
            cursor.execute("UPDATE items SET message = ?, file_id = ? WHERE id = ?", (new_message, new_file_id, item_id))
        else:
            cursor.execute("UPDATE items SET message = ? WHERE id = ?", (new_message, item_id))
        conn.commit()




def delete_item(item_id):
    conn = get_db_connection()
    with conn:

        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))

        # Обработчики команд

def get_message_by_id(item_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

def get_object_name_by_id(item_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT object_name FROM items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None




def update_message_in_db(message_id, new_text):
    try:
        # Подключение к базе данных
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Обновление текста сообщения
        cursor.execute("UPDATE messages SET text = ? WHERE id = ?", (new_text, message_id))
        conn.commit()

        # Закрытие соединения
        conn.close()
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении сообщения: {e}")
        raise e



def update_photo_in_db(photo_id, new_photo):
    try:
        # Подключение к базе данных
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Обновление данных фотографии
        cursor.execute("UPDATE photos SET data = ? WHERE id = ?", (new_photo, photo_id))
        conn.commit()

        # Закрытие соединения
        conn.close()
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении фотографии: {e}")
        raise e


def get_photo_by_id(photo_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_id FROM photos WHERE id = ?", (photo_id,))
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        else:
            return None




@bot.message_handler(commands=['start'])
def start(message):
    user = bot.get_chat(message.chat.id)
    user_id = get_user_id(message.chat.id)
    if not user_id:
        add_user(user.username, message.chat.id)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())

def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in
               ['Добавить', 'Просмотреть', 'Редактировать/Удалить', 'Отмена']]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(
    func=lambda message: message.text in ['Добавить', 'Просмотреть', 'Редактировать/Удалить', 'Отмена'])
def handle_menu_option(message):
    if message.text == 'Добавить':
        show_object_selection(message)
    elif message.text == 'Просмотреть':
        show_look_menu(message)
    elif message.text == 'Редактировать/Удалить':
        show_edit_delete_menu(message)
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
        home_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_home = types.KeyboardButton("Домой")
        home_keyboard.add(button_home)

        # Отправка сообщения с клавиатурой
        bot.reply_to(message, "Данные сохранены.", reply_markup=home_keyboard)

        # Регистрация обработчика для кнопки "Домой"
        bot.register_next_step_handler(message, start)
    else:
        bot.reply_to(message, "Вы не отправили фото.")

def show_look_menu(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in object_names.values()]
    buttons.append(types.KeyboardButton("Все объекты"))
    buttons.append(types.KeyboardButton("Домой"))
    keyboard.add(*buttons)
    msg = bot.send_message(message.chat.id, "Выберите объект для просмотра:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, look_data)
    bot.register_next_step_handler(msg, start)

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
        cursor.execute("SELECT items.message, photos.file_id "
                      "FROM items "
                      "INNER JOIN photos ON items.photo_id = photos.id "
                      "WHERE items.object_name = ? "
                      "ORDER BY items.id DESC",
                      (object_name,))
        data = cursor.fetchall()

    if data:
        for message_text, file_id in data:
            bot.send_photo(message.chat.id, file_id, caption=message_text)
    else:
        bot.send_message(message.chat.id, f"Нет данных для объекта {object_name}.")

def filter_data_by_user(message, user_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT items.object_name, items.message, photos.file_id "
                      "FROM items "
                      "INNER JOIN photos ON items.photo_id = photos.id "
                      "WHERE items.user_id = ? "
                      "ORDER BY items.id DESC",
                      (user_id,))
        data = cursor.fetchall()

    if data:
        for object_name, message_text, file_id in data:
            bot.send_photo(message.chat.id, file_id, caption=f"{object_name}: {message_text}")
    else:
        bot.send_message(message.chat.id, "У вас нет сохраненных данных.")


# Добавьте обработчик нажатия на объект в режиме редактирования
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def handle_edit_selection(call):
    # Извлекаем item_id, object_name и user_id из callback_data
    item_id = int(call.data.split("_")[1])
    object_name = call.data.split("_")[2]
    user_id = call.from_user.id

    # Вызываем process_edit_delete_selection() с нужными аргументами
    process_edit_delete_selection(item_id, object_name, user_id)

    # Обновляем сообщение пользователю
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Объект был обновлен.")


def show_edit_delete_menu(message, page=1, items_per_page=1):
    # Получаем идентификатор пользователя
    user_id = get_user_id(message.chat.id)
    if not user_id:
        # Если пользователь не зарегистрирован, отправляем сообщение
        bot.send_message(message.chat.id, "Вы не зарегистрированы в системе. Пожалуйста, используйте команду /start.")
        return

    # Подключаемся к базе данных
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        # Получаем все записи пользователя
        cursor.execute("SELECT id, object_name, message, photo_id FROM items WHERE user_id = ? ORDER BY id LIMIT ? OFFSET ?", (user_id, items_per_page, (page - 1) * items_per_page))
        items = cursor.fetchall()

    if not items:
        # Если нет записей, отправляем сообщение
        bot.send_message(message.chat.id, "У вас нет сохраненных сообщений или фотографий.")
        return

    # Перебираем записи и выводим их по одному
    for item in items:
        item_id, object_name, message_text, photo_id = item
        if object_name == "item":
            # Выводим сообщение
            bot.send_message(message.chat.id, message_text)
        elif object_name == "photo":
            # Выводим фото
            try:
                file_info = bot.get_file(photo_id)
                bot.send_photo(message.chat.id, file_info.file_id, caption=f"Фото ID: {item_id}")
            except Exception as e:
                bot.send_message(message.chat.id, f"Не удалось отобразить фото ID: {item_id}. Ошибка: {e}")

    # Создаем клавиатуру с кнопками для навигации и редактирования/удаления
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if page > 1:
        keyboard.add(types.InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"page_{page-1}"))
    if len(items) == items_per_page:
        keyboard.add(types.InlineKeyboardButton("Следующая ➡️", callback_data=f"page_{page+1}"))
    buttons = [types.InlineKeyboardButton(f"{item[0]} - {item[1]} - Редактировать", callback_data=f"edit_{item[0]}_{item[1]}") for item in items]
    buttons.extend([types.InlineKeyboardButton(f"{item[0]} - {item[1]} - Удалить", callback_data=f"delete_{item[0]}_{item[1]}") for item in items])
    keyboard.add(*buttons)
    bot.send_message(message.chat.id, "Выберите сообщение или фото для редактирования или удаления:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def handle_delete(call):
    item_id, object_name = call.data.split("_")[1:]
    # Подключаемся к базе данных
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        # Удаляем запись из базы данных
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    # Отправляем сообщение об удалении
    bot.send_message(call.message.chat.id, f"Запись с ID {item_id} была удалена.")
    # Обновляем меню с оставшимися записями
    show_edit_delete_menu(call.message)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def handle_page_navigation(call):
    page = int(call.data.split("_")[1])
    show_edit_delete_menu(call.message, page)
    bot.answer_callback_query(call.id)



@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_") or call.data.startswith("delete_"))
def handle_edit_delete_selection(call):
    # Обрабатываем выбор пользователя
    action, item_id, object_name = call.data.split("_")
    item_id = int(item_id)
    user_id = call.from_user.id

    if action == "edit":
        # Редактируем выбранный элемент
        process_edit_selection(item_id, object_name, user_id)
    elif action == "delete":
        # Удаляем выбранный элемент
        process_delete_selection(item_id, object_name, user_id)

    # Завершаем обработку callback-запроса
    bot.answer_callback_query(call.id)

def process_edit_selection(item_id, object_name, user_id):
    if object_name == "item":
        # Редактирование сообщения
        message_text = get_message_by_id(item_id)
        if message_text:
            msg = bot.send_message(user_id, f"Введите новый текст сообщения (текущий: {message_text})")
            bot.register_next_step_handler(msg, update_message, item_id, message_text)
    elif object_name == "photo":
        # Редактирование фото
        photo_data = get_photo_by_id(item_id)
        if photo_data:
            msg = bot.send_message(user_id, "Пожалуйста, отправьте новое фото")
            bot.register_next_step_handler(msg, update_photo, item_id, photo_data)
    else:
        # Некорректный тип объекта
        bot.send_message(user_id, "Некорректный тип объекта для редактирования")

def process_edit_delete_selection(item_id, object_name, user_id, text=None, photo_data=None):
    if object_name == "item":
        process_edit_selection(item_id, object_name, user_id, text)
    elif object_name == "photo":
        process_edit_selection(item_id, object_name, user_id, photo_data)


def process_delete_selection(item_id, object_name, user_id):
    if object_name == "item":
        # Удаление сообщения
        delete_item(item_id)
        bot.send_message(user_id, "Сообщение было удалено.")
    else:
        # Удаление фото
        delete_item(item_id)
        bot.send_message(user_id, "Фото было удалено.")


def update_message(new_text, item_id, object_name):
    try:
        # Обновить сообщение в базе данных
        update_message_in_db(item_id, new_text)

        # Вернуть обновленное сообщение
        updated_message = get_message_by_id(item_id)
        return updated_message

    except Exception as e:
        # Обработка ошибок
        print(f"Ошибка при обновлении сообщения: {e}")
        return None


def update_photo(new_photo, item_id, object_name):
    try:
        # Обновить фото в базе данных
        update_photo_in_db(item_id, new_photo)

        # Вернуть обновленное фото
        updated_photo = get_photo_by_id(item_id)
        return updated_photo

    except Exception as e:
        # Обработка ошибок
        print(f"Ошибка при обновлении фото: {e}")
        return None


bot.polling()




#======================================================================================================
неудачный код
 
import os
import sqlite3
from telebot import TeleBot, types
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Инициализация бота
bot = TeleBot('')

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

def get_user_id(chat_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE chat_id = ?", (chat_id,))
        user = cursor.fetchone()
        return user[0] if user else None

def process_new_message(message, item_id, object_name):
    if object_name == "item":
        new_message = message.text
        update_item(item_id, new_message)
        bot.reply_to(message, "Сообщение было обновлено.")
    else:
        new_photo_id = get_photo_by_id(item_id)
        if message.photo:
            file_id = message.photo[-1].file_id
            update_item(item_id, None, file_id)

            bot.reply_to(message, "Фото было обновлено.")
        else:
            bot.reply_to(message, "Пожалуйста, отправьте фото.")

        def update_item(item_id, new_message, new_photo_id=None):
            conn = get_db_connection()
            with conn:
                cursor = conn.cursor()
                if new_message is not None:
                    cursor.execute("UPDATE items SET message = ? WHERE id = ?", (new_message, item_id))
                if new_photo_id is not None:
                    cursor.execute("UPDATE items SET photo_id = ? WHERE id = ?", (new_photo_id, item_id))

def get_photo_by_id(item_id):
            conn = get_db_connection()
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT photo_id FROM items WHERE id = ?", (item_id,))
                photo_id = cursor.fetchone()[0]
                return photo_id

def filter_data_by_object(message, object_name):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT items.message, photos.file_id "
                               "FROM items "
                               "INNER JOIN photos ON items.photo_id = photos.id "
                               "WHERE items.object_name = ? "
                               "ORDER BY items.id DESC",
                               (object_name,))
        data = cursor.fetchall()

    if data:
        for message_text, file_id in data:
            bot.send_photo(message.chat.id, file_id, caption=message_text)
    else:
                bot.send_message(message.chat.id, f"Нет данных для объекта {object_name}.")

def filter_data_by_user(message, user_id):
            conn = get_db_connection()
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT items.object_name, items.message, photos.file_id "
                               "FROM items "
                               "INNER JOIN photos ON items.photo_id = photos.id "
                               "WHERE items.user_id = ? "
                               "ORDER BY items.id DESC",
                               (user_id,))
                data = cursor.fetchall()

            if data:
                for object_name, message_text, file_id in data:
                    bot.send_photo(message.chat.id, file_id, caption=f"{object_name}: {message_text}")
            else:
                bot.send_message(message.chat.id, "У вас нет сохраненных данных.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("filter_"))
def handle_filter_selection(call):
            filter_type = call.data.split("_")[1]
            if filter_type == "object":
                object_name = call.data.split("_")[2]
                filter_data_by_object(call.message, object_name)
            elif filter_type == "user":
                user_id = get_user_id(call.from_user.id)
                filter_data_by_user(call.message, user_id)

@bot.message_handler(commands=['filter'])
def show_filter_menu(message):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Фильтр по объекту", callback_data="filter_object"))
            markup.add(InlineKeyboardButton("Фильтр по пользователю", callback_data="filter_user"))
            bot.send_message(chat_id=message.chat.id, text="Выберите тип фильтра:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def handle_edit_selection(call):
            # Извлекаем item_id, object_name и user_id из callback_data
            item_id = int(call.data.split("_")[1])
            object_name = call.data.split("_")[2]
            user_id = call.from_user.id

            # Вызываем process_edit_delete_selection() с нужными аргументами
            process_edit_delete_selection(item_id, object_name, user_id)

            # Обновляем сообщение пользователю
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Объект был обновлен.")

def show_edit_delete_menu(message):
            user_id = get_user_id(message.chat.id)

            if user_id:
                conn = get_db_connection()
                with conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, object_name, message FROM items WHERE user_id = ?", (user_id,))
                    items = cursor.fetchall()

                if items:
                    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                    buttons = [types.KeyboardButton(f"{item[0]} - {item[1]} - Редактировать") for item in items]
                    buttons.extend([types.KeyboardButton(f"{item[0]} - {item[1]} - Удалить") for item in items])
                    buttons.append(types.KeyboardButton("Домой"))
                    keyboard.add(*buttons)
                    msg = bot.send_message(message.chat.id, "Выберите сообщение для редактирования или удаления:",
                                           reply_markup=keyboard)
                    bot.register_next_step_handler(msg, process_edit_delete_selection)
                else:
                    bot.send_message(message.chat.id, "У вас нет сохраненных сообщений.")
            else:
                bot.send_message(message.chat.id,
                                 "Вы не зарегистрированы в системе. Пожалуйста, используйте команду /start.")

        # Обработчики команд и сообщений
@bot.message_handler(commands=['start'])
def start(message):
            add_user(message.chat.username, message.chat.id)
            markup = InlineKeyboardMarkup()
            for object_name in object_names.values():
                markup.add(InlineKeyboardButton(object_name, callback_data=object_name))
            bot.send_message(chat_id=message.chat.id, text="Выберите объект:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
            object_name = call.data
            user_id = get_user_id(call.message.chat.id)
            bot.send_message(chat_id=call.message.chat.id,
                             text=f"Отправьте сообщение или фото для объекта {object_names[object_name]}.")
            bot.register_next_step_handler(call.message, handle_new_item, object_name, user_id)

def handle_new_item(message, object_name, user_id):
            photo_id = None
            if message.photo:
                file_id = message.photo[-1].file_id
                photo_id = add_photo(file_id)
            add_item(object_names[object_name], photo_id, message.text, user_id)
            bot.reply_to(message, "Объект был добавлен.")

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
            user_id = get_user_id(message.chat.id)
            if user_id is None:
                bot.reply_to(message, "Вы не зарегистрированы. Пожалуйста, нажмите /start, чтобы начать.")
                return

            # Проверяем, является ли сообщение редактированным
            if message.edit_date:
                process_new_message(message, message.message_id, "item")
            elif message.photo:
                process_new_message(message, message.message_id, "photo")

@bot.message_handler(commands=['filter'])
def handle_filter_command(message):
            show_filter_menu(message)

def main():
    create_tables()
    bot.polling()

if __name__ == '__main__':
    main()


#=================================================================================================



#базовы код
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


@bot.message_handler(commands=['help', 'weather'])
def command_handler(message):
    """
    Приветствую вас!
    help - приветствие и помощь
    /weather - открыть сайт погоды

    Для запуска бота нажми на
    запуск или на команду старт в menu
    """
    if message.text == '/help':
        bot.send_message(message.chat.id, command_handler.__doc__)
    elif message.text == '/weather':
        weather_link = 'https://yandex.ru/weather/?lat=63.71604156&lon=66.66759491&via=ssc'
        weather_keyboard = InlineKeyboardMarkup()
        weather_keyboard.add(InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
        bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)




# Словарь с доступными объектами
object_names = {
    'ПРС-10': 'ПРС-10',
    'ПРС-11': 'ПРС-11',
    'УРС-12': 'УРС-12',
    'ПРС-13': 'ПРС-13',
    'КС-5-7': 'КС 5 - 7',
    'Утт и Ст': 'Утт и Ст',
    'Другие обьекты': 'Другие обьекты'
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
    keyboard = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
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
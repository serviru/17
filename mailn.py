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
bot = telebot.TeleBot('')
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
    updater = updater(token="")
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
import os
import sqlite3
from telebot import TeleBot, types
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

import logging

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
            raise  # В случае других ошибок выбрасываем исключение

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
        if message.photo:
            file_id = message.photo[-1].file_id
            update_item(item_id, None, file_id)
            bot.reply_to(message, "Фото было обновлено.")
        else:
            bot.reply_to(message, "Пожалуйста, отправьте фото.")

def update_item(item_id, new_message, new_file_id=None):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.cursor()
            if new_file_id:
                cursor.execute("UPDATE items SET message = ?, file_id = ? WHERE id = ?", (new_message, new_file_id, item_id))
            else:
                cursor.execute("UPDATE items SET message = ? WHERE id = ?", (new_message, item_id))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error updating item: {e}")

def delete_item(item_id):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    except sqlite3.Error as e:
        logging.error(f"Error deleting item: {e}")

def delete_photo(photo_id):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    except sqlite3.Error as e:
        logging.error(f"Error deleting photo: {e}")

def get_message_by_id(item_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_object_name_by_id(item_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT object_name FROM items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_photo_by_id(photo_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_id FROM photos WHERE id = ?", (photo_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else None

@bot.message_handler(commands=['start'])
def start(update, context):
    user = update.effective_user
    if not get_user_id(update.effective_chat.id):
        add_user(user.username, update.effective_chat.id)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Добро пожаловать! Выберите действие:", reply_markup=get_main_menu_keyboard())


def get_main_menu_keyboard():
    keyboard = [[InlineKeyboardButton("Добавить", callback_data='add'),
                 InlineKeyboardButton("Просмотреть", callback_data='view')],
                [InlineKeyboardButton("Редактировать/Удалить", callback_data='edit_delete'),
                 InlineKeyboardButton("Отмена", callback_data='cancel')]]
    return InlineKeyboardMarkup(keyboard)



def handle_button_click(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'add':
        # Обработка нажатия на кнопку "Добавить"
        pass
    elif query.data == 'view':
        # Обработка нажатия на кнопку "Просмотреть"
        pass
    elif query.data == 'edit_delete':
        # Обработка нажатия на кнопку "Редактировать/Удалить"
        pass
    elif query.data == 'cancel':
        # Обработка нажатия на кнопку "Отмена"
        pass



updater = Updater(token='6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU', use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CallbackQueryHandler(handle_button_click))

updater.start_polling()



def filter_data_by_user(message, user_id):
    conn = get_db_connection()
    try:
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

    except sqlite3.Error as e:
        logging.error(f"Error filtering data by user: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def handle_edit_selection(call):
    try:
        item_id = int(call.data.split("_")[1])
        object_name = call.data.split("_")[2]
        user_id = call.from_user.id
        process_edit_selection(item_id, object_name, user_id, call)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Объект был обновлен.")
    except (ValueError, IndexError):
        logging.error(f"Error handling edit selection: {call.data}")
        bot.reply_to(call.message, "Произошла ошибка при обработке выбора редактирования.")

def show_edit_delete_menu(update, context):
    user_id = get_user_id(update.effective_chat.id)
    if user_id:
        conn = get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, object_name, message FROM items WHERE user_id = ?", (user_id,))
                items = cursor.fetchall()

            if items:
                keyboard = ReplyKeyboardMarkup([
                    [f"{item[0]} - {item[1]} - Редактировать", f"{item[0]} - {item[1]} - Удалить"]
                    for item in items
                ] + [[KeyboardButton("Домой")]], resize_keyboard=True)
                context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите сообщение для редактирования или удаления:", reply_markup=keyboard)
                context.dispatcher.add_handler(MessageHandler(Filters.text, process_edit_delete_selection))
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text="У вас нет сохраненных сообщений.")
        except sqlite3.Error as e:
            logging.error(f"Error showing edit/delete menu: {e}")
            context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка при загрузке ваших сообщений.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Вы не зарегистрированы в системе. Пожалуйста, используйте команду /start.")

def process_edit_delete_selection(update, context):
    selection = update.message.text
    if " - Редактировать" in selection:
        item_id = int(selection.split(" - ")[0])
        object_name = selection.split(" - ")[1]
        user_id = get_user_id(update.effective_chat.id)
        process_edit_selection(item_id, object_name, user_id, update)
    elif " - Удалить" in selection:
        item_id = int(selection.split(" - ")[0])
        object_name = selection.split(" - ")[1]
        user_id = get_user_id(update.effective_chat.id)
        process_delete_selection(item_id, object_name, user_id, update, context)
    elif selection == "Домой":
        start(update, context)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Некорректный выбор.")

def process_edit_selection(item_id, object_name, user_id, update, context):
    # Логика редактирования объекта
    if object_name == "item":
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите новый текст сообщения:")
        context.dispatcher.add_handler(MessageHandler(Filters.text, lambda u, c: update_message(u, c, item_id, object_name)))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Отправьте новую фотографию:")
        context.dispatcher.add_handler(MessageHandler(Filters.photo, lambda u, c: update_photo(u, c, item_id, object_name)))

def process_delete_selection(item_id, object_name, user_id, update, context):
    if object_name == "item":
        delete_item(item_id)
    else:
        delete_photo(item_id)

    context.bot.send_message(chat_id=update.effective_chat.id, text="Объект был удален.")
    show_edit_delete_menu(update, context)


def update_message(update, context, item_id, object_name):
    new_message = update.message.text
    update_item(item_id, new_message)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Сообщение обновлено.")
    show_edit_delete_menu(update, context)


def update_photo(update, context, item_id, object_name):
    new_file_id = update.message.photo[-1].file_id
    update_item(item_id, None, new_file_id)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Фотография обновлена.")
    show_edit_delete_menu(update, context)


bot.polling(non_stop=True)


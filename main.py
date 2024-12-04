import telebot
from telebot import types
import sqlite3
import os
from datetime import datetime
import time


API_TOKEN = '6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU'
bot = telebot.TeleBot(API_TOKEN)





def send_welcome(message):
    welcome_text = (
        'Приветствую вас!\n\n'
        'Вот что я могу для вас сделать:\n\n'
        '- /main - вернуться в главное меню\n'
        '- /help - получить помощь и узнать о возможностях бота\n'
        '- /weather - открыть сайт погоды\n'
        '- /incidents - узнать о происшествиях\n\n'
        'Для запуска бота нажмите на значок скрепки, чтобы прикрепить файл: photo\n, '
        'или импортируйте сюда фото из галерей своего устройства.\n\n'
        'Чтобы начать, нажмите кнопку "Меню" ниже.'
    )
    bot.send_message(message.chat.id, welcome_text)

def send_weather_info(message):
    weather_link = 'https://yandex.ru/pogoda?lat=63.71604156&lon=66.66759491'
    #weather_link = 'https://www.ventusky.com/?p=64.9;12.1;3&l=temperature-2m&t=20240501/20&src=link'
    weather_keyboard = types.InlineKeyboardMarkup()
    weather_keyboard.add(types.InlineKeyboardButton(text="Перейти на сайт погоды", url=weather_link))
    bot.send_message(message.chat.id, 'Перейдите по ссылке для просмотра погоды', reply_markup=weather_keyboard)

def send_incidents_info(message):
    incidents_channel_link = 'https://t.me/+5qJpWu1gaakyMzVi'  # Замените на актуальную ссылку на канал
    incidents_keyboard = types.InlineKeyboardMarkup()
    incidents_keyboard.add(types.InlineKeyboardButton(text="Перейти в канал Связь Общая", url=incidents_channel_link))
    bot.send_message(message.chat.id, 'Нажмите кнопку ниже, чтобы перейти в канал Связь Общая:', reply_markup=incidents_keyboard)

@bot.message_handler(commands=['help', 'weather', 'main', 'incidents'])
def command_handler(message):
    if message.text == '/help':
        send_welcome(message)
    elif message.text == '/weather':
        send_weather_info(message)
    elif message.text == '/main':
        # Здесь можно добавить логику для главного меню
        bot.send_message(message.chat.id, 'Вы в главном меню.')
    elif message.text == '/incidents':
        send_incidents_info(message)





# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    profile_photo TEXT,
                    status TEXT,
                    role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT,
                    completed INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY,
                    object_id INTEGER,
                    photo_id TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Получение всех пользователей
def get_all_users():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users;")
    users = c.fetchall()
    conn.close()
    return users

# Получение всех объектов
def get_all_objects():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM objects;")
    objects = c.fetchall()
    conn.close()
    return objects


# Обработка нажатия на кнопку "🗄 Работа с БД"
@bot.message_handler(func=lambda message: message.text == "🗄 Работа с БД")
def handle_db_work(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Добавляем кнопки по две в ряд
    markup.add("👤 Вывести пользователей", "🗑 Удалить пользователя")
    markup.add("📦 Вывести объекты", "🔄 Изменить роль")
    markup.add("🔙 Назад в главное меню")
    
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "👤 Вывести пользователей")
def show_users(message):
    chat_id = message.chat.id
    users = get_all_users()
    
    if not users:
        bot.send_message(chat_id, "🚫 Нет зарегистрированных пользователей в базе данных.")
        return
    
    response = "👥 Зарегистрированные пользователи:\n\n"
    
    for user in users:
        user_id, first_name, last_name, username, profile_photo, status, role = user
        
        # Проверка на пустые значения
        username_display = f"@{username}" if username else "Нет имени пользователя"
        full_name = f"{first_name} {last_name}".strip() or "Имя не указано"
        
        user_info = (
            f"🔹 ID: {user_id}\n"
            f"🔹 Имя: {full_name}\n"
            #f"🔹 Пользователь: {username_display}\n"
            f"🔹 Роль: {role}\n\n"
        )
        
        response += user_info

    try:
        # Сохраняем данные пользователей в файл
        with open('users.txt', 'w', encoding='utf-8') as file:
            file.write(response)  # Записываем весь ответ в файл

        # Создаем кнопки для отправки файла и возвращения в главное меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        save_button = types.KeyboardButton("📥 Скачать файл с пользователями")
        back_button = types.KeyboardButton("🔙 Назад в главное меню")
        markup.add(save_button, back_button)

        # Отправляем сообщение с пользователями
        bot.send_message(chat_id, response + "\nВы можете скачать файл с пользователями:", reply_markup=markup)

    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

@bot.message_handler(func=lambda message: message.text == "📥 Скачать файл с пользователями")
def send_file_users(message):
    chat_id = message.chat.id
    try:
        with open('users.txt', 'rb') as file:
            bot.send_document(chat_id, file)
    except FileNotFoundError:
        bot.send_message(chat_id, "🚫 Файл не найден. Пожалуйста, сначала выведите пользователей.")
    except Exception as e:
        bot.send_message(chat_id, "🚫 Ошибка при отправке файла.")
        print(f"Ошибка при отправке файла: {e}")
# Удаление пользователя
@bot.message_handler(func=lambda message: message.text == "🗑 Удалить пользователя")
def delete_user(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите ID пользователя для удаления:")
    
    # Сохраняем состояние ожидания ID пользователя для удаления
    bot.register_next_step_handler(message, confirm_delete_user)

def confirm_delete_user(message):
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный ID пользователя.")
        return
    
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    
    # Проверяем роль пользователя перед удалением
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    
    if result:
        role = result[0]
        if role == 'admin':
            bot.send_message(message.chat.id, "🚫 Пользователя с ролью 'admin' удалить нельзя.")
            conn.close()
            return
        
        # Если роль не 'admin', удаляем пользователя
        try:
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            bot.send_message(message.chat.id, f"Пользователь с ID {user_id} успешно удален.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Произошла ошибка при удалении пользователя: {str(e)}")
    else:
        bot.send_message(message.chat.id, "Пользователь с таким ID не найден.")
    
    conn.close()


# Вывод всех объектов
@bot.message_handler(func=lambda message: message.text == "📦 Вывести объекты")
def show_objects(message):
    chat_id = message.chat.id
    objects = get_all_objects()
    
    if not objects:
        bot.send_message(chat_id, "🚫 Нет объектов в базе данных.")
        return
    
    response = "Все объекты:\n"
    for obj in objects:
        obj_id, user_id, name, completed, created_at = obj
        
        # Используем эмодзи для обозначения статуса
        status = "✅ Выполнено" if completed else "❌ Не выполнено"
        
        response += f"ID: {obj_id}, \nПользователь ID: {user_id}, \nНазвание: {name}, \nСтатус: {status}, Дата создания: {created_at}\n\n"

    # Сохраняем данные объектов в файл
    with open('objects.txt', 'w', encoding='utf-8') as file:
        file.write(response)  # Записываем весь ответ в файл

    # Создаем кнопки для отправки файла и возвращения в главное меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    save_button = types.KeyboardButton("📥 Скачать файл с объектами")
    back_button = types.KeyboardButton("🔙 Назад в главное меню")
    markup.add(save_button, back_button)

    # Отправляем сообщение с объектами
    bot.send_message(chat_id, response + "\nВы можете скачать файл с объектами:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📥 Скачать файл с объектами")
def send_file_objects(message):
    chat_id = message.chat.id
    try:
        with open('objects.txt', 'rb') as file:
            bot.send_document(chat_id, file)
    except FileNotFoundError:
        bot.send_message(chat_id, "🚫 Файл не найден. Пожалуйста, сначала выведите объекты.")
    except Exception as e:
        bot.send_message(chat_id, "🚫 Ошибка при отправке файла.")
        print(f"Ошибка при отправке файла: {e}")
'''
# Обработка кнопки "🔙 Назад в главное меню"
@bot.message_handler(func=lambda message: message.text == "🔙 Назад в главное меню")
def back_to_main_menu(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Вы вернулись в главное меню. Выберите действие:", reply_markup=main_menu_markup())

def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("👤 Вывести пользователей"),
               types.KeyboardButton("📦 Вывести объекты"))
    return markup
'''
# Изменение роли пользователя
@bot.message_handler(func=lambda message: message.text == "🔄 Изменить роль")
def change_role(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите ID пользователя для изменения роли:")
    
    # Сохраняем состояние ожидания ID пользователя для изменения роли
    bot.register_next_step_handler(message, ask_new_role)

def ask_new_role(message):
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный ID пользователя.")
        return
    
    bot.send_message(message.chat.id, "Введите новую роль для пользователя:")
    
    # Сохраняем состояние ожидания новой роли
    bot.register_next_step_handler(message, confirm_change_role, user_id)

def confirm_change_role(message, user_id):
    new_role = message.text.strip()
    
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    
    try:
        c.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
        
        if c.rowcount > 0:
            bot.send_message(message.chat.id, f"Роль пользователя с ID {user_id} успешно изменена на '{new_role}'.")
        else:
            bot.send_message(message.chat.id, f"Пользователь с ID {user_id} не найден.")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка при изменении роли: {str(e)}")
    
    conn.close()

# Возврат в главное меню
@bot.message_handler(func=lambda message: message.text == "🔙 Назад в главное меню")
def back_to_main_menu(message): # type: ignore
    show_main_menu(message.chat.id)



def register_user(user_id, first_name, last_name, username, profile_photo, status, role): # type: ignore
    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO users (id, first_name, last_name, username, profile_photo, status, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, first_name, last_name, username, profile_photo, status, role))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при регистрации пользователя: {e}")
    finally:
        conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name  # Получаем имя
    last_name = message.from_user.last_name if message.from_user.last_name else ''  # Проверяем на None
    username = message.from_user.username if message.from_user.username else ''  # Проверяем на None
    profile_photo = get_profile_photo(user_id)  # Получаем фото профиля
    status = ''  # Установите значение по умолчанию для статуса

    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (user_id,))
        
        if not c.fetchone():  # Если пользователь не найден в базе данных
            bot.reply_to(message, "Введите ваш пин-код:")
            bot.register_next_step_handler(message, check_pin, user_id, first_name, last_name, username, profile_photo, status)
        else:
            bot.reply_to(message, "Вы уже зарегистрированы.")
            show_main_menu(message.chat.id)
    except sqlite3.Error as e:
        print(f"Ошибка при старте: {e}")
    finally:
        conn.close()

def get_profile_photo(user_id):
    """Получает URL последнего фото профиля пользователя."""
    photos = bot.get_user_profile_photos(user_id)
    
    if photos.total_count > 0:
        # Получаем первую фотографию (последнюю загруженную)
        file_id = photos.photos[0][-1].file_id  # type: ignore # Получаем последний размер фотографии
        return file_id  # Вы можете сохранить file_id или использовать его для дальнейших действий
    return ''  # Если фотографий нет, возвращаем пустую строку

def check_pin(message, user_id, first_name, last_name, username, profile_photo, status):
    pin_code = message.text.strip()
    role = None

    if pin_code == '0450':
        role = 'admin'
    elif pin_code == '0000':
        role = 'user'
    else:
        bot.reply_to(message, "Неверный пин-код. Попробуйте снова.")
        return

    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (user_id,))
        
        if not c.fetchone():  # Повторная проверка на регистрацию
            register_user(user_id, first_name, last_name, username, profile_photo, status, role)
            bot.reply_to(message, f"Вы зарегистрированы как {role}!")
            show_main_menu(message.chat.id)
        else:
            bot.reply_to(message, "Вы уже зарегистрированы.")
            show_main_menu(message.chat.id)
    except sqlite3.Error as e:
        print(f"Ошибка при проверке пин-кода: {e}")
    finally:
        conn.close()

def register_user(user_id, first_name, last_name, username, profile_photo, status, role):
    """Регистрация пользователя в базе данных."""
    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (id, first_name, last_name, username, profile_photo, status, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, first_name, last_name, username, profile_photo, status, role))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при регистрации пользователя: {e}")
    finally:
        conn.close()



def get_user_role(chat_id):
    conn = sqlite3.connect('bot_database.db')  # Замените на имя вашего файла базы данных
    cursor = conn.cursor()
    
    cursor.execute("SELECT role FROM users WHERE id=?", (chat_id,))
    result = cursor.fetchone()  # Получаем первую строку результата
    
    conn.close()
    
    if result:
        return result[0]  # Возвращаем роль пользователя
    else:
        return None  # Если пользователь не найден, возвращаем None

def show_main_menu(chat_id):
    user_role = get_user_role(chat_id)  # Получаем роль пользователя
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Основные кнопки для всех пользователей
    markup.add("➕ Добавить", "📄 Осмотр", "✅ Выполнено", "🔍 Поиск")

    # Добавляем кнопку "🗄 Работа с БД" только для администраторов
    if user_role == 'admin':
        markup.add("🗄 Работа с БД")

    #return markup  # Возвращаем разметку клавиатуры
    
    bot.send_message(chat_id, "🌟 Главное меню 🌟", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "➕ Добавить")
def add_object(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📦ПРС-10", "📦ПРС-11", "✨УРС-12", "📦ПРС-13", "📦Утт и Ст", "📡 Узел связи",  "🌟 КС 5 - 7", "🌟 КС 3 - 4", "🏢 Дирекция")
    bot.send_message(message.chat.id, "Выберите объект:", reply_markup=markup)
@bot.message_handler(func=lambda message: message.text in ["📦ПРС-10", "📦ПРС-11", "✨УРС-12", "📦ПРС-13", "📦Утт и Ст", "📡 Узел связи", "🌟 КС 5 - 7", "🌟 КС 3 - 4", "🏢 Дирекция"])
def choose_object(message):
    bot.send_message(message.chat.id, "📸Загрузите фото объекта:")
    bot.register_next_step_handler(message, process_photo_step, message.text)

def process_photo_step(message, object_name):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "Пожалуйста, отправьте фото объекта.")
        return

    photo_id = message.photo[-1].file_id  # Здесь не нужно проверять на наличие photo
    save_object_step(message, object_name, photo_id)

def save_object_step(message, object_name, photo_id):
    user_id = message.from_user.id

    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        c.execute("INSERT INTO objects (user_id, name, completed) VALUES (?, ?, ?)",
                  (user_id, object_name, 0))
        
        object_id = c.lastrowid
        
        c.execute("INSERT INTO photos (object_id, photo_id) VALUES (?, ?)", (object_id, photo_id))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении объекта: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении объекта.")
    finally:
        conn.close()

    bot.send_message(message.chat.id, "Объект добавлен!")
    show_main_menu(message.chat.id)


# Константы для пагинации
ITEMS_PER_PAGE = 1  # Количество объектов на странице



@bot.message_handler(func=lambda message: message.text == "📄 Осмотр")
def view_objects(message):
    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        # Получаем объекты и соответствующие имена пользователей
        c.execute('''
            SELECT o.id, o.name, o.created_at, u.first_name 
            FROM objects o 
            LEFT JOIN users u ON o.user_id = u.id 
            WHERE o.completed = 0
        ''')
        objects = c.fetchall()
        
        if not objects:
            bot.send_message(message.chat.id, "Нет доступных объектов.")
            show_main_menu(message.chat.id)
            return
        
        markup = types.InlineKeyboardMarkup()
        
        for obj in objects:
            object_id = obj[0]
            name = obj[1]
            created_at = obj[2]
            first_name = obj[3] if obj[3] else "Неизвестный"  # Если имя не указано
            
            # Форматируем дату для вывода
            date_format = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            full_date = date_format.strftime('%d %B')  # Полная дата: день месяц
            
            # Создаём текст кнопки с красивыми разделителями
            button_text = (f" {name} \n"
                           f"🔖 ID: {object_id}\n"
                           #f"📅 Создан: {full_date}\n"
                           )
            
            # Добавляем кнопку в разметку
            markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"view_{object_id}"))
        
        bot.send_message(message.chat.id, "Доступные объекты:", reply_markup=markup)
    except sqlite3.Error as e:
        print(f"Ошибка при просмотре объектов: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении объектов.")
    finally:
        conn.close()




@bot.callback_query_handler(func=lambda call: call.data.startswith("view_"))
def view_object_details(call):
    object_id = call.data.split("_")[1]
    
    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        # Получаем информацию об объекте
        c.execute("SELECT name, created_at FROM objects WHERE id=?", (object_id,))
        obj = c.fetchone()
        
        if obj:
            name = obj[0]  # Имя объекта
            created_at = obj[1]  # Дата создания
            
            # Форматируем дату для вывода
            date_format = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            full_date = date_format.strftime('%d %B %Y')  # Полная дата: день месяц год
            
            bot.send_message(call.message.chat.id, f"{name}\nСоздано: {full_date}")  # Отправляем имя и дату
            
            # Получаем все фото для данного объекта
            c.execute("SELECT photo_id FROM photos WHERE object_id=?", (object_id,))
            photos = c.fetchall()
            
            for photo in photos:
                bot.send_photo(call.message.chat.id, photo[0])  # Используем photo_id напрямую

            # Получаем роль пользователя
            user_id = call.from_user.id
            c.execute("SELECT role FROM users WHERE id=?", (user_id,))
            user_role = c.fetchone()
            
            markup = types.InlineKeyboardMarkup(row_width=2)  # Установите количество кнопок в строке
            
            markup.add(
                types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{object_id}"),
                types.InlineKeyboardButton(text="✅ Выполнить", callback_data=f"complete_{object_id}"),
                types.InlineKeyboardButton(text="Назад", callback_data="back_to_objects")  # Изменено на "back_to_objects"
            )

            # Проверяем роль пользователя и добавляем кнопку "Удалить", если роль 'admin'
            if user_role and user_role[0] == 'admin':
                markup.add(types.InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{object_id}"))

            bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)
    except sqlite3.Error as e:
        print(f"Ошибка при просмотре объекта: {e}")
    finally:
        conn.close()

# Обработчик для кнопки "Назад"
@bot.callback_query_handler(func=lambda call: call.data == "back_to_objects")
def back_to_objects(call):
    view_objects(call.message)  # Вызов функции view_objects с сообщением



@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def edit_object(call):
    object_id = call.data.split("_")[1]
    
    # Запрашиваем новое фото
    bot.send_message(call.message.chat.id, "Загрузите новое фото объекта:")
    bot.register_next_step_handler(call.message, process_new_photo_step, object_id)

def process_new_photo_step(message, object_id):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "Пожалуйста, отправьте фото объекта.")
        return

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path) # type: ignore
        
        photo_path = f"photos/{file_info.file_path.split('/')[-1]}" # type: ignore
        
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Сохраняем новое фото в базу данных
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        c.execute("INSERT INTO photos (object_id, photo_id) VALUES (?, ?)", (object_id, message.photo[-1].file_id))
        conn.commit()
        
        bot.send_message(message.chat.id, "Описание и фото объекта обновлены!")
    except Exception as e:
        print(f"Ошибка при сохранении нового фото: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении нового фото.")
    finally:
        conn.close()
    
    show_main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("complete_")) # КНОПКА выполнить
def complete_object(call):
    object_id = call.data.split("_")[1]
    
    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        # Проверяем, существует ли объект
        c.execute("SELECT id FROM objects WHERE id=?", (object_id,))
        if not c.fetchone():
            bot.send_message(call.message.chat.id, "Объект не найден.")
            return
        
        c.execute("UPDATE objects SET completed=1 WHERE id=?", (object_id,))
        conn.commit()
        
        bot.send_message(call.message.chat.id, "Объект помечен как выполненный!")
    except sqlite3.Error as e:
        print(f"Ошибка при пометке объекта как выполненного: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка при пометке объекта.")
    finally:
        conn.close()
    
    show_main_menu(call.message.chat.id)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))# УДАЛЕНИЕ ОБЬЕКТОВ
def delete_object(call):
    object_id = call.data.split("_")[1]
    
    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        # Проверяем, существует ли объект
        c.execute("SELECT id FROM objects WHERE id=?", (object_id,))
        if not c.fetchone():
            bot.send_message(call.message.chat.id, "Объект не найден.")
            return
        
        # Удаляем объект и его фотографии
        c.execute("DELETE FROM photos WHERE object_id=?", (object_id,))
        c.execute("DELETE FROM objects WHERE id=?", (object_id,))
        
        conn.commit()
        
        bot.send_message(call.message.chat.id, "Объект удален!")
    except sqlite3.Error as e:
        print(f"Ошибка при удалении объекта: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка при удалении объекта.")
    finally:
        conn.close()
    
    show_main_menu(call.message.chat.id)

@bot.message_handler(func=lambda message: message.text == "✅ Выполнено")
def completed_objects(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    
    # Изменяем запрос, чтобы извлекать также поле created_at
    c.execute("SELECT id, name, created_at FROM objects WHERE completed=1")
    objects = c.fetchall()
    
    if not objects:
        bot.send_message(message.chat.id, "У вас нет выполненных объектов.")
        show_main_menu(message.chat.id)
        return
    
    markup = types.InlineKeyboardMarkup()
    
    for obj in objects:
        object_id = obj[0]
        name = obj[1]
        created_at = obj[2]
        
        # Форматируем дату для вывода
        date_format = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        full_date = date_format.strftime('%d %B')  # Полная дата: день месяц
        
        # Добавляем кнопку с именем объекта и датой создания
        button_text = (f" {name} \n"
                           f"🔖 ID: {object_id}\n"
                           #f"📅 Создан: {full_date}\n"
                           )
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"completed_{object_id}"))
    
    bot.send_message(message.chat.id, "Ваши выполненные объекты:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("completed_"))
def completed_object_details(call):
    object_id = call.data.split("_")[1]
    
    try:
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        # Запрос для получения имени и даты создания
        c.execute("SELECT name, created_at FROM objects WHERE id=?", (object_id,))
        obj = c.fetchone()
        
        if obj:
            name = obj[0]  # Имя объекта
            created_at = obj[1]  # Дата создания
            
            # Форматируем дату для вывода
            date_format = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            full_date = date_format.strftime('%d %B %Y')  # Полная дата: день месяц год
            
            bot.send_message(call.message.chat.id, f"{name}\nСоздано: {full_date}")  # Отправляем имя и дату
            
            # Получаем все фото для данного объекта
            c.execute("SELECT photo_id FROM photos WHERE object_id=?", (object_id,))
            photos = c.fetchall()
            
            if photos:
                for photo in photos:
                    photo_id = photo[0]
                    try:
                        # Отправляем фото по прямому пути
                        bot.send_photo(call.message.chat.id, photo_id)
                    except Exception as e:
                        bot.send_message(call.message.chat.id, f"Ошибка при отправке фото: {e}")
            else:
                bot.send_message(call.message.chat.id, "Нет фотографий для этого объекта.")
        else:
            bot.send_message(call.message.chat.id, "Объект не найден.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении деталей объекта: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка при получении деталей объекта.")
    finally:
        conn.close()



@bot.message_handler(func=lambda message: message.text == "🔍 Поиск")
def search_objects(message):
    object_list = [
        "📦 ПРС-10",
        "📦 ПРС-11",
        "✨ УРС-12",
        "📦 ПРС-13",
        "📦 Утт и Ст",
        "📡 Узел связи",
        "🌟 КС 5 - 7",
        "🌟 КС 3 - 4",
        "🏢 Дирекция"
    ]
    
    formatted_object_list = "\n".join([f"{i + 1}. {obj}" for i, obj in enumerate(object_list)])
    
    bot.send_message(message.chat.id, f"Введите номер объекта для поиска от 1 до 9 \n\n где 1  это ПРС-10 :  \n\nСписок доступных объектов:\n\n{formatted_object_list}")
    bot.register_next_step_handler(message, process_search_step, object_list)

# Обработка шага поиска
def process_search_step(message, object_list):
    if message.text == "🔙 Назад в поиск":
        search_objects(message)
        return
    elif message.text == "🏠 Главное меню":
        show_main_menu(message.chat.id)  # Предполагается, что у вас есть функция для отображения главного меню
        return

    try:
        choice = int(message.text.strip())
        
        if 1 <= choice <= len(object_list):
            selected_object = object_list[choice - 1]
            search_query = selected_object.split(" ")[-1]  # Извлекаем название объекта для поиска
            
            conn = sqlite3.connect('bot_database.db')
            c = conn.cursor()

            c.execute("SELECT id, name, created_at FROM objects WHERE name LIKE ?", (f'%{search_query}%',))
            results = c.fetchall()

            if not results:
                bot.send_message(message.chat.id, "Объекты не найдены.")
                show_main_menu(message.chat.id)
                return

            markup = types.InlineKeyboardMarkup()
            response_message = "Результаты поиска:\n"

            for obj in results:
                object_id = obj[0]
                name = obj[1]
                created_at = obj[2]
                
                date_format = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                full_date = date_format.strftime('%d %B')
                
                button_text = (f"{name}\n"
                               f"🔖 ID: {object_id}\n"
                               #f"📅 Создан: {full_date}"
                               )
                
                markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"completed_{object_id}"))
            
            # Добавляем кнопки "Назад в поиск" и "Главное меню"
            back_button = types.KeyboardButton("🔙 Назад в поиск")
            main_menu_button = types.KeyboardButton("🏠 Главное меню")
            back_markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(back_button, main_menu_button)

            bot.send_message(message.chat.id, response_message.strip(), reply_markup=markup)
            bot.send_message(message.chat.id, "Если хотите вернуться к выбору объектов или в главное меню, нажмите соответствующую кнопку ниже:", reply_markup=back_markup)
        else:
            bot.send_message(message.chat.id, "Некорректный номер. Пожалуйста, выберите номер из списка.")
            search_objects(message)

    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер объекта.")
        search_objects(message)

# Функция для обработки нажатия на кнопку "Назад в поиск"
@bot.message_handler(func=lambda message: message.text == "🔙 Назад в поиск")
def back_to_search(message):
    search_objects(message)

# Функция для обработки нажатия на кнопку "Главное меню"
@bot.message_handler(func=lambda message: message.text == "🏠 Главное меню")
def back_to_main_menu(message):
    show_main_menu(message.chat.id)  # Предполагается, что у вас есть функция для отображения главного меню


    
# Обработчик для команды "✉️ Сообщения"
@bot.message_handler(func=lambda message: message.text == "✉️ Сообщения")
def user_messages(message):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()

    # Получаем всех пользователей с их фамилиями
    c.execute("SELECT last_name FROM users")
    users_list = c.fetchall()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    message_text = "Выберите пользователя для просмотра сообщений по фамилии:\n"

    for user in users_list:
        last_name = user[0]
        message_text += f"Фамилия: {last_name}\n"
        markup.add(last_name)  # Добавляем фамилию в клавиатуру

    markup.add("Отмена")

    # Отправляем пользователю сообщение со списком пользователей
    bot.send_message(message.chat.id, message_text, reply_markup=markup)
    
    conn.close()

# Обработчик для выбора пользователя по фамилии и просмотра его объектов
@bot.message_handler(func=lambda message: message.text.strip() != "" and not message.text.isdigit())
def view_messages_by_last_name(message):
    last_name_to_search = message.text.strip()
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()

    # Проверяем, существует ли пользователь с данной фамилией
    c.execute("SELECT id FROM users WHERE last_name=?", (last_name_to_search,))
    user_row = c.fetchone()
    
    if not user_row:
        bot.send_message(message.chat.id, "Пользователь не найден.")
        return

    user_id_to_search = user_row[0]  # Получаем ID пользователя по фамилии

    # Получаем все объекты этого пользователя
    c.execute("SELECT id, name, description FROM objects WHERE user_id=?", (user_id_to_search,))
    objects = c.fetchall()

    if not objects:
        bot.send_message(message.chat.id, "Нет объектов для этого пользователя.")
        return

    # Отправляем информацию о каждом объекте
    for object_id, object_name, description in objects:
        bot.send_message(message.chat.id, f"Объект: {object_name}\nОписание: {description}")

        # Получаем все фотографии по этому объекту
        c.execute("SELECT photo_id FROM photos WHERE object_id=?", (object_id,))
        photos_rows = c.fetchall()

        if photos_rows:
            for photo in photos_rows:
                bot.send_photo(message.chat.id, photo[0])  # Отправляем фотографию
        else:
            bot.send_message(message.chat.id, "Фото: Нет доступных фотографий.")

    show_main_menu(message.chat.id)
    conn.close()




@bot.message_handler(func=lambda message: message.text == "Отмена")
def cancel(message):
   show_main_menu(message.chat.id)

def main():
    while True:
        try:
            print("Бот запущен. Ожидание сообщений...")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Произошла ошибка: {e}. Перезапуск бота через 5 секунд...")
            time.sleep(5)  # Ждем 5 секунд перед перезапуском



if __name__ == '__main__':
   bot.polling(none_stop=True)



'''

import os
import sqlite3
from telebot import TeleBot, types
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Инициализация бота
bot = TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите опцию:", reply_markup=main_menu())

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Добавить', 'Просмотреть', 'Выполнено', 'Отмена')
    return markup

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, 
                     'Приветствую вас!nnКоманды бота:n/main - вернуться в главное менюn/help - приветствие и помощьn/weather - открыть сайт погоды')

@bot.message_handler(func=lambda message: message.text in ['Добавить', 'Просмотреть', 'Выполнено', 'Отмена'])
def handle_menu_option(message):
    if message.text == 'Добавить':
        show_object_selection(message)
    elif message.text == 'Просмотреть':
        show_object_selection_for_view(message)
    elif message.text == 'Выполнено':
        show_object_selection_for_completion(message)
    elif message.text == 'Отмена':
        start(message)

def show_object_selection(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for obj in object_names.keys():
        markup.add(obj)
    markup.add('Назад')
    bot.send_message(message.chat.id, "Выберите объект для добавления:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in object_names.keys())
def handle_object_selection(message):
    bot.send_message(message.chat.id, f"Вы выбрали: {message.text}. Пожалуйста, отправьте фото.")
    bot.register_next_step_handler(message, handle_photo_upload, message.text)

@bot.message_handler(content_types=['photo'])
def handle_photo_upload(message, object_name):
    if message.photo:
        file_id = message.photo[-1].file_id
        photo_id = add_photo(file_id)
        
        bot.send_message(message.chat.id, "Введите сообщение или описание для фото:")
        bot.register_next_step_handler(message, lambda msg: save_item(msg, object_name, photo_id))
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте фото. Если хотите отменить, нажмите 'Отмена'.")
        bot.register_next_step_handler(message, handle_photo_upload, object_name)

def save_item(message, object_name, photo_id):
    user_id = message.from_user.id
    message_text = message.text
    add_item(object_name, photo_id, message_text, user_id)
    bot.send_message(message.chat.id, "Объект успешно добавлен!", reply_markup=main_menu())

def show_object_selection_for_view(message):
    markup = InlineKeyboardMarkup(row_width=3)
    for obj in object_names.keys():
        markup.add(InlineKeyboardButton(text=obj, callback_data=f"view_{obj}_1"))
    markup.add(InlineKeyboardButton(text='Назад', callback_data='back'))
    bot.send_message(message.chat.id, "Выберите объект для просмотра:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_'))
def handle_view_object(call):
    object_name, page = call.data.split('_')[1], int(call.data.split('_')[2])
    
    items_per_page = 1  # Показываем по 2 объекта за раз
    conn = get_db_connection()
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM items WHERE object_name = ? AND user_id = ?", (object_name, call.from_user.id))
    total_items = cursor.fetchone()[0]
    
    cursor.execute("SELECT items.id AS item_id, items.message, photos.file_id FROM items JOIN photos ON items.photo_id = photos.id WHERE object_name = ? AND user_id = ? LIMIT ? OFFSET ?", 
                   (object_name, call.from_user.id, items_per_page, (page - 1) * items_per_page))
    items = cursor.fetchall()
    
    if items:
        for item in items:
            item_id, description, photo_id = item
            bot.send_photo(call.message.chat.id, photo_id, caption=description)
        
        # Создание кнопок навигации
        pagination_markup = InlineKeyboardMarkup()
        if page > 1:
            pagination_markup.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"view_{object_name}_{page-1}"))
        if total_items > page * items_per_page:
            pagination_markup.add(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"view_{object_name}_{page+1}"))
        
        bot.send_message(call.message.chat.id, "Навигация:", reply_markup=pagination_markup)
    else:
        bot.send_message(call.message.chat.id, "У вас нет добавленных объектов этого типа.")
    
    bot.answer_callback_query(call.id)

# Функция для отображения выполненных объектов
def show_completed_items(message):
    conn = get_db_connection()
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT items.id AS item_id, items.message, photos.file_id FROM items JOIN photos ON items.photo_id = photos.id WHERE user_id = ?", (message.from_user.id,))
    
    items = cursor.fetchall()
    
    if items:
        for i in range(0, len(items), 3):  # По 1 сообщения в ряд
            row_markup = InlineKeyboardMarkup(row_width=2)
            for j in range(2):
                if i + j < len(items):
                    item = items[i + j]
                    item_id = item[0]
                    description = item[1]
                    photo_id = item[2]
                    row_markup.add(InlineKeyboardButton(text=f"Объект {item_id}", callback_data=f"view_completed_{item_id}"))
                    bot.send_photo(message.chat.id, photo_id, caption=description)
            bot.send_message(message.chat.id, "Навигация:", reply_markup=row_markup)
        
        bot.send_message(message.chat.id, "Все выполненные объекты отображены.")
    else:
        bot.send_message(message.chat.id, "У вас нет выполненных объектов.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_completed_'))
def handle_view_completed(call):
    item_id = int(call.data.split('_')[2])
    
    conn = get_db_connection()
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT message, photos.file_id FROM items JOIN photos ON items.photo_id = photos.id WHERE items.id = ?", (item_id,))
    
    item = cursor.fetchone()
    
    if item:
        description = item[0]
        photo_id = item[1]
        
        bot.send_photo(call.message.chat.id, photo_id, caption=description)
        
        bot.answer_callback_query(call.id)
    else:
        bot.send_message(call.message.chat.id, "Объект не найден.")

# Новый метод для выбора объекта при выполнении
def show_object_selection_for_completion(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for obj in object_names.keys():
        markup.add(obj)
    markup.add('Назад', 'Отмена')  # Добавляем кнопку "Отмена"
    bot.send_message(message.chat.id, "Выберите объект для выполнения:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in object_names.keys() and message.text != 'Назад' and message.text != 'Отмена')
def handle_completion_selection(message):
    # Здесь можно добавить логику для обработки выполнения выбранного объекта
    bot.send_message(message.chat.id, f"Вы выбрали объект: {message.text}. Объект помечен как выполненный!")
    
    # Здесь вы можете добавить логику для обновления статуса в базе данных
    
    bot.send_message(message.chat.id, "Выберите следующую опцию:", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == 'Отмена')  # Обработчик для кнопки "Отмена"
def handle_cancel(message):
    bot.send_message(message.chat.id, "Операция отменена. Вернитесь в главное меню.", reply_markup=main_menu())

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
            pass

def add_photo(file_id):
    conn = get_db_connection()
    with conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO photos (file_id) VALUES (?)", (file_id,))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
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
            time.sleep(0.5)
            with conn:
                conn.execute("INSERT INTO items (object_name, photo_id, message, user_id) VALUES (?, ?, ?, ?)",
                             (object_name, photo_id, message, user_id))
        else:
            raise e

if __name__ == '__main__':
    create_tables()
    bot.polling(none_stop=True)

#==================================================================================

import os
import sqlite3
from timeit import main
from telebot import TeleBot, types
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# Инициализация бота

bot = TeleBot('6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU')


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



# Словарь с доступными объектами
object_names = {
    'ПРС-10': 'ПРС-10',
    'ПРС-11': 'ПРС-11',
    'УРС-12': 'УРС-12',
    'ПРС-13': 'ПРС-13',
    'КС 5 - 7': 'КС 5 - 7',
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

if __name__ == '__main__':
    create_tables()
    print("Запуск бота...")
    while True:
        try:
            bot.polling(non_stop=True)
        except Exception as e:
            print(f"Ошибка при запуске бота: {e}")
            time.sleep(10)




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
        bot.send_message(message.chat.id, command_handler.__doc__) # type: ignore
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
        start(message)
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
    #buttons.append(types.KeyboardButton("Отмена"))  # Заменяем "Домой" на "Отмена"
    #keyboard.add(*buttons)
    msg = bot.send_message(message.chat.id, "Выберите объект для просмотра:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, handle_look_menu_response)  # Обработчик ответа

def handle_look_menu_response(message):
    if message.text == "Отмена":
        bot.send_message(message.chat.id, "Вы отменили выбор.")  # Сообщение об отмене
        return  # Выходим из функции, ничего не делаем дальше
    
    elif message.text in object_names.values() or message.text == "Все объекты":
        look_data(message)  # Если выбран объект, вызываем look_data
    else:
        bot.send_message(message.chat.id, "Неверный выбор. Пожалуйста, выберите объект или нажмите 'Отмена'")
        show_look_menu(message)  # Показываем меню снова после неверного выбора



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
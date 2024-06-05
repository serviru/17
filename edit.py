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
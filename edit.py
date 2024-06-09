from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import sqlite3
from telebot.types import InputMediaPhoto
from telegram.update import Update
import telebot
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler, MessageHandler, Filters, Dispatcher



def startt(update, context):
    # Создаем инлайн-клавиатуру с кнопками в ряд по две, адаптируясь к ширине экрана
    keyboard = [
        [InlineKeyboardButton("Изменить", callback_data='to change', resize_keyboard=True, width=1)]
         #InlineKeyboardButton("Удалить", callback_data='delete', resize_keyboard=True, width=1)],
        #[InlineKeyboardButton("Отмена", callback_data='cancel', resize_keyboard=True, width=1)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True)

    # Отправляем сообщение с инлайн-клавиатурой
    context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите действие:", reply_markup=reply_markup)

    # Регистрируем обработчик для обработки нажатий на кнопки
    context.dispatcher.add_handler(CallbackQueryHandler(button_click))

def button_click(update, context):
    query = update.callback_query
    query.answer()  # Удаляем индикатор загрузки



    if query.data == 'to change':
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

            # Добавляем новые кнопки для редактирования
            buttons = [
                [InlineKeyboardButton("Изменить", callback_data='change')],
                [InlineKeyboardButton("Удалить", callback_data='delete_message')],
                [InlineKeyboardButton("Назад", callback_data='back')]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

            # Получаем текущий индекс и список результатов
            current_index = context.user_data.get('current_index', 0)
            results = context.user_data.get('results', [])

            # Получаем информацию об объекте
            object_name, file_id, message = results[current_index]

            # Отправляем сообщение с новыми кнопками
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Редактирование объекта: {object_name}\n\nСообщение: {message}",
                reply_markup=reply_markup
            )

        elif query.data == 'back':
            # Получаем список результатов и сбрасываем индекс текущего сообщения
            results = context.user_data.get('results', [])
            context.user_data['current_index'] = 0

            # Отправляем первое сообщение
            send_message(update, context, results, 0)

        elif query.data == 'delete_message':
            # Получаем текущий индекс и список результатов
            current_index = context.user_data.get('current_index', 0)
            results = context.user_data.get('results', [])

            # Получаем информацию об объекте
            object_name, file_id, message = results[current_index]

            # Создаем новое соединение с базой данных для этого потока
            conn = sqlite3.connect('database.db')
            c = conn.cursor()

            # Удаляем объект из базы данных
            c.execute("DELETE FROM items WHERE object_name = ?", (object_name,))
            conn.commit()

            # Закрываем соединение с базой данных
            conn.close()

            # Получаем список результатов и сбрасываем индекс текущего сообщения
            results = context.user_data.get('results', [])
            context.user_data['current_index'] = 0

            # Отправляем первое сообщение
            send_message(update, context, results, 0)

        elif query.data == 'change':
            # Получаем текущий индекс и список результатов
            current_index = context.user_data.get('current_index', 0)
            results = context.user_data.get('results', [])

            # Получаем информацию об объекте
            object_name, file_id, message = results[current_index]

            # Отправляем сообщение, чтобы пользователь мог изменить фото и текст
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Пожалуйста, отправьте новое фото и сообщение для этого объекта."
            )

            # Устанавливаем состояние "изменение объекта"
            context.user_data['editing_object'] = {
                'object_name': object_name,
                'file_id': file_id,
                'message': message
            }

            return ConversationHandler.EDIT

    elif query.data == 'save':
        # Получаем текущий индекс и список результатов
        current_index = context.user_data.get('current_index', 0)
        results = context.user_data.get('results', [])

        # Получаем информацию об объекте
        object_name, file_id, message = results[current_index]

        # Создаем новое соединение с базой данных для этого потока
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Сохраняем изменения в базе данных
        c.execute("UPDATE items SET object_name = ?, message = ? WHERE object_name = ?",
                  (object_name, message, object_name))
        conn.commit()

        # Закрываем соединение с базой данных
        conn.close()

        # Отправляем сообщение о сохранении
        context.bot.send_message(chat_id=query.message.chat_id, text="Изменения сохранены.")

        # Вызываем функцию show_message_actions, чтобы обновить сообщение
        show_message_actions(update, context)

    elif query.data == 'select':
        # Обработка кнопки "Выбрать"
        handle_select(update, context)



    elif query.data == 'cancel':
        # Получаем список результатов и сбрасываем индекс текущего сообщения
        results = context.user_data.get('results', [])
        context.user_data['current_index'] = 0

        # Отправляем первое сообщение
        send_message(update, context, results, 0)




def send_message(update, context, results, index):
    object_name, file_id, message = results[index]

    # Создаем инлайн-клавиатуру с кнопками "Предыдущий", "Следующий" и "Выбрать"
    keyboard = [
        [InlineKeyboardButton("Предыдущий", callback_data='prev', resize_keyboard=True, width=1),
         InlineKeyboardButton("Следующий", callback_data='next', resize_keyboard=True, width=1)],
        [InlineKeyboardButton("Выбрать", callback_data='select', resize_keyboard=True, width=1)]
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

# Обработчик для кнопки "Выбрать"
def handle_select(update, context):
    # Обрабатываем нажатие на кнопку "Выбрать"
    query = update.callback_query
    query.answer()

    # Получаем текущий индекс и список результатов из контекста пользователя
    current_index = context.user_data.get('current_index', 0)
    results = context.user_data.get('results', [])

    # Проверяем, есть ли результаты в списке
    if results:
        try:
            # Получаем информацию об объекте
            object_name, file_id, message = results[current_index]

            # Редактируем существующее сообщение
            if file_id:
                context.bot.edit_message_media(
                    chat_id=update.effective_chat.id,
                    message_id=query.message.message_id,
                    media=InputMediaPhoto(file_id, caption=f"{object_name}\n{message}")
                )
            else:
                context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=query.message.message_id,
                    text=f"{object_name}\n{message}"
                )

            # Вызываем функцию show_message_actions(), чтобы отобразить новые кнопки
            show_message_actions(update, context)
        except IndexError:
            # Если текущий индекс выходит за пределы списка результатов,
            # отправляем сообщение об этом
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="К сожалению, нет результатов для отображения."
            )
    else:
        # Если список результатов пуст, отправляем сообщение об этом
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="К сожалению, нет результатов для отображения."
        )


def show_message_actions(update, context):
    # Получаем индекс текущего сообщения из контекста пользователя
    current_index = context.user_data.get('current_index', 0)
    results = context.user_data.get('results', [])

    # Создаем инлайн-клавиатуру с кнопками "Изменить", "Сохранить", "Удалить" и "Назад"
    keyboard = [
        [InlineKeyboardButton("Изменить", callback_data='edit', resize_keyboard=True, width=1),
         InlineKeyboardButton("Сохранить", callback_data='save', resize_keyboard=True, width=1),
         InlineKeyboardButton("Удалить", callback_data='delete', resize_keyboard=True, width=1)],
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


def edit(update, context):
    # Обработка кнопки "Изменить"
    query = update.callback_query
    query.answer()

    # Получаем текущий индекс и список результатов
    current_index = context.user_data.get('current_index', 0)
    results = context.user_data.get('results', [])

    # Получаем информацию об объекте
    object_name, file_id, message = results[current_index]

    # Отправляем сообщение с кнопками "Сохранить" и "Отмена"
    keyboard = [
        [InlineKeyboardButton("Сохранить", callback_data='save', resize_keyboard=True, width=1)],
        [InlineKeyboardButton("Отмена", callback_data='cancel', resize_keyboard=True, width=1)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True)

    if file_id:
        context.bot.edit_message_media(
            chat_id=update.effective_chat.id,
            message_id=query.message.message_id,
            media=InputMediaPhoto(file_id, caption=f"{object_name}\n{message}"),
            reply_markup=reply_markup
        )
    else:
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=query.message.message_id,
            text=f"{object_name}\n{message}",
            reply_markup=reply_markup
        )

def save(update, context):
    # Обработка кнопки "Сохранить"
    query = update.callback_query
    query.answer()

    # Здесь вы можете добавить код для сохранения изменений

    # Возвращаем пользователя к основному сообщению
    show_message_actions(update, context)

def cancel(update, context):
    # Обработка кнопки "Назад"
    query = update.callback_query
    query.answer()

    # Возвращаем пользователя к основному сообщению
    show_message_actions(update, context)


def main():
    updater = Updater(token='6625466018:AAFbUtVtlMJ6g8Oip1msrgwhWzKOxRLosiU', use_context=True)
    dispatcher = updater.dispatcher

    # Регистрируем обработчики команд и callback-ов
    dispatcher.add_handler(CommandHandler("startt", startt))
    dispatcher.add_handler(CallbackQueryHandler(button_click))
    dispatcher.add_handler(CallbackQueryHandler(handle_select, pattern='select'))
    dispatcher.add_handler(CallbackQueryHandler(edit, pattern='edit'))
    dispatcher.add_handler(CallbackQueryHandler(save, pattern='save'))
    dispatcher.add_handler(CallbackQueryHandler(cancel, pattern='cancel'))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text='Сделать транскрипцию видео')
    builder.button(text='Извлечь субтитры из видео')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def cancel_input_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text='Отменить текущий ввод')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def skip_time_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text='Пропустить', callback_data='skip_time_input')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
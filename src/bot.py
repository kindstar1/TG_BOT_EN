import random
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from sqlalchemy import select, and_

from .config import TELEGRAM_BOT_TOKEN
from .database import SessionLocal
from .models import Users, MainWords, UserWords


print("Start telegram bot...")
state_storage = StateMemoryStorage()

bot = TeleBot(TELEGRAM_BOT_TOKEN, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []

def show_hint(*lines):
    return "\n".join(lines)

def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

class Command:
    ADD_WORD = "Добавить слово ➕"
    DELETE_WORD = "Удалить слово🔙"
    NEXT = "Дальше ⏭"

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()
    guessing_word = State()
    delete_word_rus = State()

def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print('New user detected, who hasn\'t used "/start" yet')
        return 0
@bot.message_handler(commands=["cards", "start"])
def create_cards(message):
    ses = SessionLocal() 
    tg_id = message.from_user.id
    user = ses.query(Users).filter_by(user_id=tg_id).first()
    if user is None:
        user = Users(user_id=tg_id)
        ses.add(user)
        start_word = ses.query(MainWords).all()
        for word in start_word:
            assoc = UserWords(
                user_id=user.user_id, mword_id=word.mword_id, dlt_flag=False
            )
            ses.add(assoc)
        ses.commit()
        cid = message.chat.id
        bot.send_message(cid, "Hello, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)
    global buttons
    buttons = []
    active_user_words = (
        ses.query(UserWords).filter_by(user_id=tg_id, dlt_flag=False).all()
    )
    q = (
        select(MainWords.rus_word, MainWords.en_word)
        .join(UserWords)
        .where(and_(UserWords.user_id == user.user_id, UserWords.dlt_flag == False))
    )
    res = ses.execute(q).all()
    random_tupples = random.sample(res, 4)
    fix_first = random_tupples[0]
    target_word = fix_first[1]
    translate = fix_first[0]
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others_tup = random_tupples[1:]
    others = [t[1] for t in others_tup]
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])
    markup.add(*buttons)
    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.guessing_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["target_word"] = target_word
        data["translate_word"] = translate
        data["other_words"] = others
    ses.close()

@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word_first_step(message):
    bot.set_state(message.from_user.id, MyStates.delete_word_rus, message.chat.id)
    bot.send_message(message.chat.id, "Введите слово на русском, которое хотите удалить:")

@bot.message_handler(state=MyStates.delete_word_rus)
def delete_word_second_step(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["rus_word"] = message.text
    russ_word = data["rus_word"]
    tg_id = message.from_user.id
    ses = SessionLocal()
    q = (
        select(MainWords.rus_word)
        .join(UserWords)
        .where(and_(UserWords.user_id == tg_id, MainWords.rus_word == russ_word))
    )
    result = ses.execute(q).all()
    if len(result)!= 0:
        change_flg = ses.query(UserWords).join(MainWords).filter(and_(
            UserWords.user_id == tg_id, MainWords.rus_word == russ_word)).first()
        change_flg.dlt_flag = True
        ses.commit()
        bot.send_message(message.chat.id, "Слово удалено")
    else:
        bot.send_message(message.chat.id, "Нет такого слова на изучении")
    ses.close()
    bot.delete_state(message.from_user.id, message.chat.id)

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word_first_step(message):
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    bot.send_message(
        message.chat.id, "Введите слово на русском, которое хотите добавить:")

@bot.message_handler(state=MyStates.target_word)
def add_word_second_step(message):
    bot.set_state(message.from_user.id, MyStates.translate_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["rus_word"] = message.text
    bot.send_message(message.chat.id, "Теперь введите перевод слова:")

@bot.message_handler(state=MyStates.translate_word)
def add_word_third_step(message):
    ses = SessionLocal()
    eng_word = message.text
    tg_id = message.from_user.id
    user = ses.query(Users).filter_by(user_id=tg_id).first()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        russ_word = data["rus_word"]
    ses = SessionLocal() 
    existing_word = ses.query(MainWords).filter_by(rus_word=russ_word).first()
    if existing_word is None:
        existing_word = MainWords(rus_word=russ_word, en_word=eng_word)
        ses.add(existing_word)
        ses.commit()
    assoc_2 = UserWords(
        user_id=user.user_id, mword_id=existing_word.mword_id, dlt_flag=False
    )
    ses.add(assoc_2)
    ses.commit()
    bot.send_message(message.chat.id, f"Слово успешно добавлено в словарь!")
    ses.close()
    bot.delete_state(message.from_user.id, message.chat.id)

@bot.message_handler(state=MyStates.guessing_word, func=lambda message: True, content_types=["text"])
def message_reply(message):
    text = message.text
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if "target_word" not in data:
            return
        target_word = data["target_word"]
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            hint_msg = show_hint(*hint_text)
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            markup.add(
                types.KeyboardButton(Command.NEXT),
                types.KeyboardButton(Command.ADD_WORD),
                types.KeyboardButton(Command.DELETE_WORD),
            )
            bot.send_message(message.chat.id, hint_msg, reply_markup=markup)
            bot.delete_state(message.from_user.id, message.chat.id)
        else:
            all_variants = [data["target_word"]] + data.get("other_words", [])
            if text not in all_variants:
                return
            hint = show_hint(
                "Допущена ошибка!",
                f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}",
            )
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            for btn in buttons:
                if btn.text == text:
                    markup.add(types.KeyboardButton(text + "❌"))
                else:
                    markup.add(btn)
            bot.send_message(message.chat.id, hint, reply_markup=markup)

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)
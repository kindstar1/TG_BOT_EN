import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import engine, SessionLocal
from src.models import Base, MainWords

def create_tables(engine):
    Base.metadata.drop_all(engine) 
    Base.metadata.create_all(engine)

def insert_random_words(session):
    dict_word = {
        "Мир": "Peace", "Зеленый": "Green", "Белый": "White", "Машина": "Car",
        "Собака": "Dog", "Кошка": "Cat", "Дом": "House", "Книга": "Book",
        "Вода": "Water", "Солнце": "Sun",
    }
    if session.query(MainWords).count() == 0:
        for rus, eng in dict_word.items():
            session.add(MainWords(rus_word=rus, en_word=eng))
        session.commit()
        print("Начальные слова добавлены.")
    else:
        print("Слова уже существуют, добавление пропущено.")

print("Инициализация БД...")

create_tables(engine)

ses = SessionLocal()
insert_random_words(ses)
ses.close()

print("Инициализация завершена.")
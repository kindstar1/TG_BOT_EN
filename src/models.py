import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    user_id = sq.Column(sq.Integer, primary_key=True)

class MainWords(Base):
    __tablename__ = "mainwords"
    mword_id = sq.Column(sq.Integer, primary_key=True)
    rus_word = sq.Column(sq.String(length=100), unique=True)
    en_word = sq.Column(sq.String(length=100), unique=True)

class UserWords(Base):
    __tablename__ = "userwords"
    word_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("users.user_id"), nullable=False)
    mword_id = sq.Column(sq.Integer, sq.ForeignKey("mainwords.mword_id"), nullable=False)
    user = relationship(Users, backref="user_words")
    mword = relationship(MainWords, backref="main_words")
    dlt_flag = sq.Column(sq.Boolean, nullable=False, default=False)
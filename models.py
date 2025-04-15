from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)

    # Связь с книгами
    books = db.relationship('Book', backref='user', lazy=True)

    # Связь с фильмами
    movies = db.relationship('Movie', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


# Модель книги
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Book {self.title}>"


# Модель фильма
class Movie(db.Model):
    imdbID = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    poster = db.Column(db.String(255), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Movie {self.title}>"

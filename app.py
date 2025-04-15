from flask import Flask, render_template, request, redirect, url_for
import requests
import random
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Настройки базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    # Связь с книгами
    books = db.relationship('Book', backref='user', lazy=True)

    # Связь с фильмами
    movies = db.relationship('Movie', backref='user', lazy=True)


# Модель книги
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Модель фильма
class Movie(db.Model):
    imdbID = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    poster = db.Column(db.String(255), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Загрузка пользователя по ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Функция для поиска фильмов через OMDb API
def get_movies(query=None):
    api_key = "e1fe4f87"  # Здесь вставь свой ключ API OMDb
    url = f"http://www.omdbapi.com/?s={query}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    if data['Response'] == 'True':
        return data['Search']
    return []


# Функция для поиска книг через Google Books API
def get_books(query=None):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    data = response.json()

    if 'items' in data:
        books = []
        for item in data['items']:
            book_info = item['volumeInfo']
            books.append({
                'id': item.get('id'),  # <-- ВАЖНО: добавляем ID книги
                'title': book_info.get('title', 'No Title'),
                'image': book_info.get('imageLinks', {}).get('thumbnail', ''),
                'description': book_info.get('description', 'No description available.')
            })
        return books
    return []


# Список случайных запросов для фильмов и книг
random_books_queries = ["Harry Potter", "The Great Gatsby", "1984", "Moby Dick", "The Catcher in the Rye"]
random_movies_queries = ["Inception", "The Dark Knight", "Titanic", "The Godfather", "Avatar"]


@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.form.get('search')
    books = []
    movies = []

    if search_query:
        books = get_books(search_query)
        movies = get_movies(search_query)
    else:
        random_book_query = random.choice(random_books_queries)
        random_movie_query = random.choice(random_movies_queries)
        books = get_books(random_book_query)
        movies = get_movies(random_movie_query)

    return render_template('index.html', books=books, movies=movies)


@app.route('/books', methods=['GET', 'POST'])
def books():
    search_query = request.form.get('search')
    books = []

    if search_query:
        books = get_books(search_query)
    else:
        random_book_query = random.choice(random_books_queries)
        books = get_books(random_book_query)

    return render_template('books.html', books=books)


@app.route('/movies', methods=['GET', 'POST'])
def movies():
    search_query = request.form.get('search')
    movies = []

    if search_query:
        movies = get_movies(search_query)
    else:
        random_movie_query = random.choice(random_movies_queries)
        movies = get_movies(random_movie_query)

    return render_template('movies.html', movies=movies)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('profile'))
        else:
            return "Неверный логин или пароль"

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Пользователь уже существует"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/book/<book_id>')
def book_detail(book_id):
    url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
    response = requests.get(url)
    book = response.json().get("volumeInfo", {})
    return render_template("book_detail.html", book=book)


@app.route('/movie/<imdb_id>')
def movie_detail(imdb_id):
    api_key = "e1fe4f87"
    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={api_key}&plot=full"
    response = requests.get(url)
    movie = response.json()
    return render_template("movie_detail.html", movie=movie)


# Функции для добавления фильмов и книг в профиль
@app.route('/add_book/<book_id>')
@login_required
def add_book(book_id):
    url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
    response = requests.get(url)
    book_info = response.json().get("volumeInfo", {})

    if book_info:
        new_book = Book(
            title=book_info['title'],
            image=book_info['imageLinks'].get('thumbnail', ''),
            description=book_info.get('description', 'No description available.'),
            user_id=current_user.id
        )
        db.session.add(new_book)
        db.session.commit()
    return redirect(url_for('profile'))


@app.route('/add_movie/<imdb_id>')
@login_required
def add_movie(imdb_id):
    api_key = "e1fe4f87"
    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={api_key}&plot=full"
    response = requests.get(url)
    movie_info = response.json()

    if movie_info:
        new_movie = Movie(
            imdbID=movie_info['imdbID'],
            title=movie_info['Title'],
            poster=movie_info['Poster'],
            year=movie_info['Year'],
            user_id=current_user.id
        )
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for('profile'))


# Создание базы данных при первом запуске
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

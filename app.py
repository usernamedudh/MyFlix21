from flask import Flask, render_template, request, redirect, url_for
import requests
import random
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import SubmitField, FileField, StringField
from wtforms.validators import DataRequired, Email

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Модели
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    books = db.relationship('Book', backref='user', lazy=True)
    movies = db.relationship('Movie', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



class Movie(db.Model):
    imdbID = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    poster = db.Column(db.String(255), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('Save Changes')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Функции для работы с Wikipedia и Wikidata API
def get_wikipedia_page_title(name):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": name,
        "format": "json"
    }
    response = requests.get(url, params=params).json()
    results = response.get("query", {}).get("search", [])
    if results:
        return results[0]["title"]
    return None


def get_wikidata_id(wiki_title):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": wiki_title,
        "prop": "pageprops",
        "format": "json"
    }
    response = requests.get(url, params=params).json()
    pages = response['query']['pages']
    for page in pages.values():
        return page.get('pageprops', {}).get('wikibase_item')
    return None


def get_person_image(wikidata_id):
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
    response = requests.get(url).json()
    try:
        entity = response['entities'][wikidata_id]
        image_name = entity['claims']['P18'][0]['mainsnak']['datavalue']['value']
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{image_name.replace(' ', '_')}"
    except Exception:
        return None


def get_person_image_from_name(name):
    title = get_wikipedia_page_title(name)
    if not title:
        return None
    wikidata_id = get_wikidata_id(title)
    if not wikidata_id:
        return None
    return get_person_image(wikidata_id)


# API-запросы
def get_movies(query=None):
    api_key = "e1fe4f87"
    url = f"http://www.omdbapi.com/?s={query}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    return data['Search'] if data['Response'] == 'True' else []


def get_books(query=None):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    data = response.json()
    if 'items' in data:
        books = []
        for item in data['items']:
            book_info = item['volumeInfo']
            books.append({
                'id': item.get('id'),
                'title': book_info.get('title', 'No Title'),
                'image': book_info.get('imageLinks', {}).get('thumbnail', ''),
                'description': book_info.get('description', 'No description available.')
            })
        return books
    return []


random_books_queries = ["Harry Potter", "The Great Gatsby", "1984", "Moby Dick", "The Catcher in the Rye"]
random_movies_queries = ["Inception", "The Dark Knight", "Titanic", "The Godfather", "Avatar"]


# Маршруты
import os
from werkzeug.utils import secure_filename


# Папка для загрузки файлов
UPLOAD_FOLDER = os.path.join('static', 'profile_pics')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.profile_picture.data:
            file = form.profile_picture.data
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            current_user.profile_picture = filename

        db.session.commit()
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', form=form)


@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.form.get('search')
    if search_query:
        books = get_books(search_query)
        movies = get_movies(search_query)
    else:
        books = get_books(random.choice(random_books_queries))
        movies = get_movies(random.choice(random_movies_queries))
    return render_template('index.html', books=books, movies=movies)


@app.route('/books', methods=['GET', 'POST'])
def books():
    search_query = request.form.get('search')
    if search_query:
        books = get_books(search_query)
    else:
        books = get_books(random.choice(random_books_queries))
    return render_template('books.html', books=books)



@app.route('/movies', methods=['GET', 'POST'])
def movies():
    search_query = request.form.get('search')
    if search_query:
        movies = get_movies(search_query)
    else:
        movies = get_movies(random.choice(random_movies_queries))
    return render_template('movies.html', movies=movies)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('profile'))
        return "Неверный логин или пароль"
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            return "Пользователь уже существует"
        new_user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/book/<book_id>', methods=['GET', 'POST'])
def book_detail(book_id):
    url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
    response = requests.get(url)
    book_data = response.json()
    book = book_data.get("volumeInfo", {})
    reviews = Review.query.filter_by(book_id=book_id).all()

    author_name = book.get('authors', [None])[0]
    author_image = get_person_image_from_name(author_name) if author_name else None

    return render_template("book_detail.html", book=book, book_id=book_id, reviews=reviews, author_image=author_image)


@app.route('/submit_review/<book_id>', methods=['POST'])
@login_required
def submit_review(book_id):
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    review = Review(book_id=book_id, user_id=current_user.id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    return redirect(url_for('book_detail', book_id=book_id))


@app.route('/movie/<imdb_id>')
def movie_detail(imdb_id):
    api_key = "e1fe4f87"
    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={api_key}&plot=full"
    response = requests.get(url)
    movie = response.json()

    first_actor = movie.get('Actors', '').split(',')[0].strip()
    actor_image = get_person_image_from_name(first_actor) if first_actor else None

    return render_template("movie_detail.html", movie=movie, actor_image=actor_image)


@app.route('/add_book/<book_id>')
@login_required
def add_book(book_id):
    url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
    response = requests.get(url)
    info = response.json().get("volumeInfo", {})
    if info:
        new_book = Book(
            title=info.get('title', 'No Title'),
            image=info.get('imageLinks', {}).get('thumbnail', ''),
            description=info.get('description', 'No description'),
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
    info = response.json()
    if info:
        new_movie = Movie(
            imdbID=info['imdbID'],
            title=info['Title'],
            poster=info['Poster'],
            year=info['Year'],
            user_id=current_user.id
        )
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for('profile'))


# Инициализация базы данных
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)

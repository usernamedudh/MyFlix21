import requests

# 🔑 Сюди встав свій OMDb API ключ
OMDB_API_KEY = "e1fe4f87"

# Отримання фільмів з OMDb API
def get_movies(query):
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={query}"
    response = requests.get(url)
    data = response.json()
    movies = []

    if data.get('Response') == 'True':
        for movie in data.get('Search', []):
            movies.append(movie.get('Title'))

    return movies

# Отримання книг з Google Books API
def get_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    data = response.json()
    books = []

    for item in data.get('items', []):
        title = item.get('volumeInfo', {}).get('title')
        if title:
            books.append(title)

    return books

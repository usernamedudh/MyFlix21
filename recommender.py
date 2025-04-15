from utils import get_books, get_movies

# Пример функции get_recommendations для книг и фильмов
def get_recommendations(category):
    # Пример данных для книг и фильмов (заменены на реальные ссылки)
    if category == 'книги':
        return [
            {
                'title': 'The Great Gatsby',
                'image': 'https://link_to_image.jpg',
                'description': 'A novel written by American author F. Scott Fitzgerald.',
                'info_link': 'https://www.goodreads.com/book/show/4671.The_Great_Gatsby'
            },
            {
                'title': 'To Kill a Mockingbird',
                'image': 'https://link_to_image2.jpg',
                'description': 'A novel by Harper Lee published in 1960.',
                'info_link': 'https://www.goodreads.com/book/show/2657.To_Kill_a_Mockingbird'
            }
        ]
    elif category == 'фильмы':
        return [
            {
                'title': 'The Shawshank Redemption',
                'image': 'https://link_to_movie_image.jpg',
                'description': 'Two imprisoned men bond over a number of years...',
                'info_link': 'https://www.imdb.com/title/tt0111161/'
            },
            {
                'title': 'The Godfather',
                'image': 'https://link_to_movie_image2.jpg',
                'description': 'The aging patriarch of an organized crime dynasty...',
                'info_link': 'https://www.imdb.com/title/tt0068646/'
            }
        ]

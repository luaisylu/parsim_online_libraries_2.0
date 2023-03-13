import argparse
import os.path
import time
import json
from pathlib import Path 
from urllib.parse import urljoin
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def check_for_redirect(response, folder='books/'):
    if response.history:
        raise requests.exceptions.HTTPError

      
def parse_book_page(response, book_page_url):
    html_code = BeautifulSoup(response.text, 'lxml')
    book_author_and_title_selector = 'h1'
    book_author_and_title = html_code.select_one(book_author_and_title_selector).text
    book_name, book_author = book_author_and_title.split("::")
    book_name = book_name.strip()
    book_author = book_author.strip()
    image_url_selector = "div.bookimage img"
    image_url = html_code.select_one(image_url_selector)["src"]
    image_link = urljoin(book_page_url, image_url)
    book_comments_selector = 'div.texts span.black'
    book_comments = html_code.select(book_comments_selector)
    book_genres_selector = 'span.d_book a'
    book_genres = html_code.select(book_genres_selector)
    
    book_comments = ''.join([comment.text for comment in book_comments])
    book_genres = ''.join([genre.text for genre in book_genres])
    book ={
        "title" : book_name,
        "autor" : book_author,
        "img_src" : image_link,
        "comments" : book_comments,
        "genres" : book_genres
    }
    
    return book


def get_books_urls(args):
    book_urls  = []
    for page in range(args.start_page, args.end_page):
        site_page_links = f"https://tululu.org/l55/{page}"
        page_response = requests.get(site_page_links)
        html_code = BeautifulSoup(page_response.text, 'lxml')
      
        cards_html_code_selector = "table.d_book"
        cards_html_code = html_code.select(cards_html_code_selector)
        for card_html_code in cards_html_code:
            book_id = card_html_code.find("a")["href"]
            full_link = urljoin("https://tululu.org", book_id)
            book_urls.append(full_link)
    return book_urls


def download_txt(file_path, book_response):
    with open(file_path, 'wb') as file:
        file.write(book_response.content)


def download_img(image_link, folder_images):
    image_file_name = urlparse(image_link).path.split('/')[-1]
    image_path = os.path.join(folder_images, image_file_name)
    response = requests.get(image_link)
    response.raise_for_status()
    with open(image_path, 'wb') as file:
        file.write(response.content)


def download_json(json_path, book):
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(book, json_file, ensure_ascii=False)

      
def main():
    parser = argparse.ArgumentParser(
        description='Программа по парсингу страницы и дальнейшее их загрузки'
    )
    parser.add_argument(
        'start_page',
        type=int,
        help='Первая страница',
        default=1
    )
    parser.add_argument(
        'end_page',
        type=int,
        help='Последняя страница',
        default=5
    )
    parser.add_argument(
        '--dest_folder',
        help='Путь к каталогу',
        default="media"
    )
    parser.add_argument(
        '--skip_imgs',
        action='store_true',
        help='Не скачивать картинки'
    )
    parser.add_argument(
        '--skip_txt',
        action='store_true',
        help='Не скачивать книги'
    )
    parser.add_argument(
        '--json_path',
        help='Указать свой путь к *.json файлу',
        default="information"
    )
    args = parser.parse_args()
    
    book_folder = os.path.join(args.dest_folder, "books")
    Path(book_folder).mkdir(parents=True, exist_ok=True)

    images_folder = os.path.join(args.dest_folder, "image")
    Path(images_folder).mkdir(parents=True, exist_ok=True)
    
    books_urls = get_books_urls(args)
    for book_url in books_urls:
        book_id = book_url.split("https://tululu.org/b")[1].split("/")[0]
        params ={
            "id": book_id
        }
        book_page_url = f"https://tululu.org/b{book_id}/"
        try:
            text_url="https://tululu.org/txt.php"
            book_response = requests.get(text_url, params=params)
            book_response.raise_for_status()
            check_for_redirect(book_response)
            book_page_response = requests.get(book_page_url)
            book_page_response.raise_for_status()
            
            book = parse_book_page(book_page_response, book_page_url)
            book_name = book["title"]
            image_link = book["img_src"]
            check_for_redirect(book_page_response)
            book["book_path"] = os.path.join(book_folder, book_name)
            
            if not args.skip_imgs:
                download_img(image_link, images_folder)
            if not args.skip_txt:
                download_txt(book["book_path"], book_response)
            
        except requests.exceptions.HTTPError:
            print("Такой книги нет", book_id)
        except ValueError:
            print("Ошибка кода")
        except ConnectionError:
            print("Ошибка соединения")
            time.sleep(20)
        json_folder = args.json_path 
        Path(json_folder).mkdir(parents=True, exist_ok=True)
        json_path = os.path.join(json_folder, "books_information.json")
        download_json(json_path, book)

        
if __name__ == "__main__":  
    main()

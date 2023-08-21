import os
import datetime
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from collections import defaultdict
from http.server import HTTPServer, SimpleHTTPRequestHandler

import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server, shell



def on_reload():
    with open ('index.html', 'r', encoding="utf8") as file:
        return file.read()


def main():
    with open("books_information.json", "r", encoding="utf8") as my_file:
        books_information = my_file.read()

    books = json.loads(books_information)
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html'])
    )
    template = env.get_template('template.html')

    rendered_page = template.render(
        books = books
    )
    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)
    server_change = Server()
    server_change.watch('index.html', on_reload)
    server_change.serve(root='.')
    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()
    
 


if __name__ == '__main__':
    main()
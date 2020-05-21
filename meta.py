"""
Python 3.7

Написать скрипт на python который будет парсить 10 первых статей с сайта habr.com.
Для каждой полученной статьи нужно получить ее название,
ссылку на статью и общее количество символов в тексте статьи.

10 полученных записей (название/ссылка/кол-во символов) нужно добавить в список в trello.
Т.е. каждая запись будет представлять из себя карточку в trello, где название карточки будет
формироваться из названия статьи и кол-ва символов в статье, а в описание карточки
trello нужно записать ссылку на статью.

При повторном запуске скпипта, в trello не должно образоваться дублей.

Раздел habr.com, который нужно распартись и взять 10 первых статей:
https://m.habr.com/ru/hub/python/top/

Скрипт должен быть написан на ЯП python3 и оформлен в виде одного файла <название>.py
Для написания скрипта можно использовать любые open source библиотеки.
"""

import requests
from bs4 import BeautifulSoup

# scrape params
URL = 'https://habr.com/ru/hub/python/top/'
ARTICLE_COUNT = 1

# trello params
API_KEY = 'fde2a8d0e518d164ee95d6aaccba06b8'
OAUTH_TOKEN = 'd447bf4c504a6845b38540f89834a8ffc8da61d6df9d40750aaa7a4733f98c80'
BOARD_NAME = 'meta'
LIST_NAME = 'articles'


class DidntFindRequestElement(Exception):
    pass


def check_response_errors(response):
    """Check response status code and raise http error if not 200"""
    try:
        response.raise_for_status()
    except requests.HTTPError as exception:
        print(exception)
        raise


def get_habr_request(url):
    """Send GET request to specified url"""
    response = requests.get(url)
    check_response_errors(response)
    return response.text


def parse_response(response, count):
    """Parse html and get name, link and count symbols for each post"""
    articles = BeautifulSoup(
        response, features='html.parser'
    ).find_all('h2', {'class': 'post__title'})[:count]
    collect_articles = {}
    for article in articles:
        name = article.find('a').text
        link = article.find('a').get('href')
        post = BeautifulSoup(
            get_habr_request(link), features='html.parser'
        ).find('div', {'class': 'post__text'})
        symbols = len(post.text) if post else 0
        collect_articles['{} {}'.format(name, symbols)] = link
    return collect_articles


def request_trello(url):
    """Send GET request to trello with access params"""
    response = requests.get(
        url, params={
            'key': API_KEY, 'token': OAUTH_TOKEN, 'response_type': 'token'
        }, timeout=30
    )
    check_response_errors(response)
    return response.json()


def get_trello_board():
    """Get trello board id"""
    boards = request_trello('https://api.trello.com/1/members/me/boards')
    return find_id(boards, BOARD_NAME)


def get_trello_list(board_id):
    """Get trello list id"""
    lists = request_trello('https://api.trello.com/1/boards/{}/lists'.format(board_id))
    return find_id(lists, LIST_NAME)


def find_id(response, name):
    """Find desired item"""
    for element in response:
        if element['name'] == name:
            return element['id']
    raise DidntFindRequestElement


def get_existing_trello_cards(list_id):
    """Find desired item"""
    cards = request_trello('https://api.trello.com/1/lists/{}/cards'.format(list_id))
    return {
        card['name']: card['desc'] for card in cards
    }


def create_new_card(list_id, card_name, desc):
    response = requests.post(
        'https://api.trello.com/1/cards', params={
            'key': API_KEY,
            'token': OAUTH_TOKEN,
            'name': card_name,
            'idList': list_id,
            'desc': desc
        }, timeout=30)
    check_response_errors(response)


def create_trello_tickets(articles_info):
    board_id = get_trello_board()
    list_id = get_trello_list(board_id)
    existing_cards = get_existing_trello_cards(list_id)
    for card_name, desc in articles_info.items():
        if card_name not in existing_cards:
            create_new_card(list_id, card_name, desc)


def scrape():
    """The main function to start scraping and creating tickets"""
    response = get_habr_request(URL)
    articles_info = parse_response(response, ARTICLE_COUNT)
    if articles_info:
        create_trello_tickets(articles_info)
    else:
        print('Something wrong with Habr, I dont see any posts there')
        raise DidntFindRequestElement


if __name__ == '__main__':
    scrape()

import grequests
import requests
from bs4 import BeautifulSoup


class Parser:
    def __init__(self, category_url):
        self.__main_page = "https://www.velostrana.ru/"
        self.__category_url = category_url

    def test(self):
        response = requests.get(f'{self.__main_page}{self.__category_url}')
        with open('test.html', 'w', encoding='utf-8') as file:
            file.write(response.text)


def main():
    parser = Parser('veloaksessuary')
    parser.test()


if __name__ == '__main__':
    main()

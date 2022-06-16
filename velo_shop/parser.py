import grequests
import requests
import os
import csv
from bs4 import BeautifulSoup


class Parser:

    def __init__(self):
        self.__main_site_url = 'https://kzn.velo-shop.ru'

    def parse_category_urls(self):
        response = requests.get(self.__main_site_url + '/catalog')
        soup = BeautifulSoup(response.text, 'lxml')
        categories = soup.find('div', class_='catalog_section_list').find_all('a', class_='thumb')
        categories_dict = dict()
        for category in categories:
            url = category.get('href')
            name = category.find('img').get('alt')
            categories_dict[name] = url
        return categories_dict

    def parse(self):
        categories_dict = self.parse_category_urls()[:-1]
        for key, value in categories_dict.items():
            csv_headers = []
            csv_products = []
            print(f'Parsing : {key}')
            paginations_urls = []
            paginations_urls.append(f'{self.__main_site_url}{value}')
            try:
                category_page_to_get_paginations_num = requests.get(f'{self.__main_site_url}{value}')
                pagination_count = \
                    int(BeautifulSoup(category_page_to_get_paginations_num.text, 'lxml').find('span',
                                                                                              class_='nums').find_all(
                        'a')[
                        -1:][0].text)
                for pagination in range(2, pagination_count + 1):
                    # print(f'Parsing page #{pagination}')
                    paginations_urls.append(f'https://kzn.velo-shop.ru{value}?PAGEN_1={pagination}')
            except AttributeError:
                print(f'{key} category have 1 page')
            responses_from_pagination = (grequests.get(url) for url in paginations_urls)
            resp_from_pagination = grequests.map(responses_from_pagination, size=16)
            product_urls = self.parse_product_urls(resp_from_pagination)
            print(f'Start parsing product urls')
            product_responses_grequests = (grequests.get(prod_url) for prod_url in product_urls)
            products_responses = grequests.map(product_responses_grequests, size=15)
            for product in products_responses:
                data = self.parse_product_page(product)

    def parse_product_page(self, product_response):
        data = dict()
        soup = BeautifulSoup(product_response.text, 'lxml')
        return data

    def parse_product_urls(self, resp_from_pagination):
        product_urls = []
        for response in resp_from_pagination:
            soup = BeautifulSoup(response.text, 'lxml')
            urls = soup.find('div', class_='catalog_block').find_all('div', class_='catalog_item_wrapp')
            for elem in urls:
                url = elem.find('div', class_='item-title').find('a').get('href')
                product_urls.append(url)
        return product_urls


def main():
    parser = Parser()
    parser.parse()


if __name__ == '__main__':
    main()

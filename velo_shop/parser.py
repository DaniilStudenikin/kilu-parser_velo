import json

import grequests
import requests
import os
import csv
from bs4 import BeautifulSoup


class Parser:

    def __init__(self):
        self.__main_site_url = 'https://kzn.velo-shop.ru'
        self.__attributes_id = dict()
        self.__iteration = 0
        self.__attribute_number = 1
        self.__global_attributes = ['Бренд', 'Ход амортизатора, мм', 'Год', 'Серия', 'Материал рамы', 'Тип вилки',
                                    'Тип амортизатора', 'Блокировка амортизатора', 'Диаметр колес', 'Тормоза',
                                    'Количество скоростей', 'Пол/возраст', 'Размер', 'Основной цвет',
                                    'Уровень оборудования', 'Мощность мотора, Вт', 'Шагомер', 'Калории', 'Вибро режим',
                                    'Частота сердечных сокращений', 'Световой поток в люменах',
                                    'Возможность обновления прошивки', 'Рекомендовано для фитнеса', 'Влагозащита',
                                    'Барометрический альтиметр', 'Баллы SWOLF', 'Русифицирован', 'Плавучесть',
                                    'Возможность установки карт', 'Использование карт памяти', 'Электронный компас',
                                    'Garmin Connect', 'Возможность использования в море', 'Тип карт памяти', 'Глонасс',
                                    'Загруженные карты', 'Соответствие требованиям RoHS',
                                    'Использование в малой авиации',
                                    'Крепление на пояс']
        self.__global_attributes = set(self.__global_attributes)

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
        categories_dict = self.parse_category_urls()
        categories_dict.pop('РАСПРОДАЖА')
        categories_dict.pop('ПОДАРОЧНЫЕ КАРТЫ')
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
            resp_from_pagination = grequests.map(responses_from_pagination, size=14)
            product_urls = self.parse_product_urls(resp_from_pagination)
            print(f'Start parsing product urls')
            print(product_urls)
            product_responses_grequests = (grequests.get(f'{self.__main_site_url}{prod_url}') for prod_url in
                                           product_urls)
            products_responses = grequests.map(product_responses_grequests, size=15)
            for product in products_responses:
                try:
                    print(f'Iteration #{self.__iteration} .... URL: {product.url}')
                except AttributeError:
                    print(products_responses)
                data = self.parse_product_page(product, key)
                print(f'{product.url} parse done!')
                self.__iteration += 1
                if len(data.keys()) == 0:
                    continue
                for elem in data.keys():
                    if not csv_headers.__contains__(elem):
                        csv_headers.append(elem)
                csv_products.append(data)
            if not os.path.exists(f'data/{key}'):
                os.makedirs(f'data/{key}')
            with open(f'data/{key}/{key}.csv', 'a', encoding='utf-8', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=csv_headers, restval=None)
                writer.writeheader()
                print(f'Len: {len(csv_products)}')
                for row in csv_products:
                    writer.writerow(row)

    def parse_product_page(self, product_response, category):
        data = dict()
        soup = BeautifulSoup(product_response.text, 'lxml')
        try:
            data['SKU'] = soup.find(itemprop='sku').get('content')
        except AttributeError:
            with open('products_not_found_sku.txt', 'a', encoding='utf-8') as file:
                file.write(f'Product url {product_response.url} SKU NOT FOUND!\n')
            return data
        data['Categories'] = category
        data['Name'] = soup.find('h1', {'id': 'pagetitle'}).text.strip()
        data['Regular price'] = soup.find(itemprop='price').get('content')

        # images
        images = ''
        scripts = soup.find_all('script')
        for script in scripts:
            if 'JCCatalogElement' in script.text:
                text_script = script.text.strip()
                json_ = text_script.split('new JCCatalogElement(')[1].strip()
                json_ = json_.split(');')[0].strip()
                json_ = json_.replace("'", '"')
                jsonObj = json.loads(json_)
                slider = jsonObj['OFFERS'][0]['SLIDER']
                if len(slider) == 0:
                    images += f"{self.__main_site_url}{jsonObj['OFFERS'][0]['NO_PHOTO']['SRC']}"
                    with open('products_not_found_sku.txt', 'a', encoding='utf-8') as file:
                        file.write(f'Url with no photo product : {product_response.url}\n')
                        file.write(f'Url of photo : {images}\n')
                    data['Images'] = images
                else:
                    for slide in slider:
                        images += f"https://kzn.velo-shop.ru{slide['SRC']},"
                    data['Images'] = images[:-1]
        table = soup.find('table', class_='props_list').find_all('tr')
        for tr in table:
            attribute_name = tr.find("td", class_="char_name").text.strip()
            attribute_value = tr.find("td", class_="char_value").text.strip()
            if self.__attributes_id.get(attribute_name) is None:
                self.__attributes_id[attribute_name] = self.__attribute_number
                self.__attribute_number += 1
            data[f'Attribute {self.__attributes_id.get(attribute_name)} name'] = attribute_name
            data[f'Attribute {self.__attributes_id.get(attribute_name)} value(s)'] = attribute_value
            data[f'Attribute {self.__attributes_id.get(attribute_name)} visible'] = 1
            if attribute_name in self.__global_attributes:
                data[f'Attribute {self.__attributes_id.get(attribute_name)} global'] = 1
            else:
                data[f'Attribute {self.__attributes_id.get(attribute_name)} global'] = 0

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

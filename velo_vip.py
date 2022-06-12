import csv
import os

import grequests
import requests
from bs4 import BeautifulSoup


class Parser:
    def __init__(self):
        self.__attribute_number = 1
        self.__main_page = 'https://www.velostrana.ru'
        self.__attributes_id = dict()
        self.__iteration = 0

    def parse_urls(self):
        url = f"{self.__main_page}/vip/woman/"
        urls_to_grequests_paginations = []
        product_urls = []
        for number in range(1, 36):
            urls_to_grequests_paginations.append(f'{url}{number}.html')
        responses_urls = (grequests.get(ur) for ur in urls_to_grequests_paginations)
        resps = grequests.map(responses_urls, size=16)
        for resp in resps:
            soup = BeautifulSoup(resp.text, 'lxml')
            print(resp.url)
            urls_products = soup.find('div', class_='product-grid _wide').find_all('div', class_='product-grid__item')

            for elem in urls_products:
                url = elem.find('a', class_='product-card__title')
                product_urls.append(url.get('href'))
        return product_urls

    def parse(self):
        urls = self.parse_urls()
        product_urls = []
        for elem in urls:
            product_urls.append(f'{self.__main_page}{elem}')
        responses = (grequests.get(url) for url in product_urls)
        resps = grequests.map(responses, size=14)
        sub_category_products_data = []
        sub_category_headers = []
        category_name = "VIP"
        self.__attributes_id = dict()
        self.__attribute_number = 1
        for resp in resps:
            print(f'Iteration #{self.__iteration} .... URL: {resp.url}')
            data = self.parse_product_by_page(resp.text, 'VIP')
            self.__iteration += 1
            for elem in data.keys():
                if not sub_category_headers.__contains__(elem):
                    sub_category_headers.append(elem)
            sub_category_products_data.append(data)
        if not os.path.exists(f'data/{category_name}'):
            os.makedirs(f'data/{category_name}')
        with open(f'data/{category_name}/{category_name}.csv', 'a', encoding='utf-8', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=sub_category_headers, restval=None)
            writer.writeheader()
            print(f'Len: {len(sub_category_products_data)}')
            for row in sub_category_products_data:
                writer.writerow(row)

    def parse_product_by_page(self, page, sub_cat_name):
        data = dict()
        category = f'Велосипеды > {sub_cat_name}'
        data['Categories'] = category
        soup = BeautifulSoup(page, 'lxml')
        try:
            name = soup.find('div', class_='productfull__header-title').find('h1').text
        except AttributeError:
            return dict()
        data['Name'] = name

        regular_price = str()
        sale_price = str()
        try:
            regular_price = soup.find('div', class_='productfull__pricebox-top').find('div',
                                                                                      class_='productfull__price-old').text[
                            :-2].strip().replace(' ', '')
            sale_price = soup.find('div', class_='productfull__price').find('div',
                                                                            class_='productfull__price-new').text[
                         :-2].strip().replace(' ', '')
            data['In stock?'] = 1
        except AttributeError:
            in_stock = soup.find('span', class_='productfull__instock _none')
            if in_stock is not None:
                regular_price = None
                # return dict()
                data['In stock?'] = 0
            else:
                regular_price = soup.find('div', class_='productfull__price').find('div',
                                                                                   class_='productfull__price-new').text[
                                :-2].strip().replace(' ', '')
                data['In stock?'] = 1
            sale_price = None
        data['Sale price'] = sale_price
        data['Regular price'] = regular_price
        try:
            data['SKU'] = soup.find('div', class_='productfull__code').text.replace('Артикул:', '').strip()
        except AttributeError:
            data['SKU'] = None
        try:
            description = soup.find('div', class_='productfull__desc textbox').find('div', class_='textbox').text[
                          20:].strip()
            data['Description'] = description
        except AttributeError:
            data['Description'] = None
        try:
            images = soup.find('div', class_='productfull-gallery').find_all('a')
            img_ulr = ''
            for image in images[:-1]:
                img_ulr += f"{self.__main_page}{image.get('href')},"
            data['Images'] = img_ulr[:-1]
        except AttributeError:
            data['Images'] = None
        tables = soup.find_all('div', class_='productfull__specification-section')[1:]

        for table in tables:
            trs = table.find('table', class_='productfull__specification-table').find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                try:
                    tds[0].find('div', class_='hintbox').extract()
                    attribute_name = tds[0].find('div', class_='productfull__specification-name').text.strip()
                    attribute_value = tds[1].text.strip()
                except AttributeError:
                    attribute_name = tds[0].find('div', class_='productfull__specification-name').text.strip()
                    attribute_value = tds[1].text.strip()
                if self.__attributes_id.get(attribute_name) is None:
                    self.__attributes_id[attribute_name] = self.__attribute_number
                    self.__attribute_number += 1
                data[f'Attribute {self.__attributes_id.get(attribute_name)} name'] = attribute_name
                data[f'Attribute {self.__attributes_id.get(attribute_name)} value(s)'] = attribute_value
                data[f'Attribute {self.__attributes_id.get(attribute_name)} visible'] = 1
                data[f'Attribute {self.__attributes_id.get(attribute_name)} global'] = 0
        return data


def main():
    parser = Parser()
    parser.parse()


if __name__ == '__main__':
    main()

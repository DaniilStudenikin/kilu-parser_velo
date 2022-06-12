import grequests
import requests
from bs4 import BeautifulSoup
import os
import csv


class Parser:
    def __init__(self, category_url, category_name):
        self.__main_page = "https://www.velostrana.ru/"
        self.__category_url = category_url
        self.__category_name = category_name
        self.__attributes_id = dict()
        self.__iteration = 0

    def parse_categories(self):
        response = requests.get(f'{self.__main_page}{self.__category_url}')
        soup = BeautifulSoup(response.text, 'lxml')
        categories = soup.find('div', class_='tab-grid').find_all('div', class_='tab-grid__item')
        cats = dict()
        for elem in categories:
            category_name = elem.find('div', class_='category-card__title').text.strip()
            category_url = elem.find('a', class_='category-card').get('href')
            print(f'Name : {category_name} .... Url: {category_url}\n')
            cats[category_name] = category_url
        return cats

    def parse(self):
        categories = self.parse_categories()
        for k, v in categories.items():
            sub_category_products_data = []
            sub_category_headers = []
            self.__attributes_id = dict()
            self.__attribute_number = 1
            category_url = f'{self.__main_page}{v}'
            category_name = k
            urls = self.parse_sub_categories_to_get_product_urls(category_url, v)
            print('Urls parsed! Starting scrap product pages!')
            responses = (grequests.get(url) for url in urls)
            resps = grequests.map(responses, size=15)
            for response in resps:
                try:
                    print(f'Iteration #{self.__iteration} .... URL: {response.url}')
                except AttributeError:
                    print(response)
                print(response.status_code)
                data = self.parse_product_by_page(response.text, k)
                print(data)
                if len(data.keys()) == 0:
                    continue
                self.__iteration += 1
                for elem in data.keys():
                    if not sub_category_headers.__contains__(elem):
                        sub_category_headers.append(elem)
                sub_category_products_data.append(data)
            cat_name = category_name.replace('/', '').replace(' ', '_')
            if not os.path.exists(f'data/{self.__category_url}/{cat_name}'):
                os.makedirs(f'data/{self.__category_url}/{cat_name}')
            with open(f'data/{self.__category_url}/{cat_name}/{cat_name}.csv', 'w', encoding='utf-8',
                      newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=sub_category_headers, restval=None)
                writer.writeheader()
                for row in sub_category_products_data:
                    writer.writerow(row)
            # print(f'Headers : {sub_category_headers}')
            # print(f'Headers len : {len(sub_category_headers)}')
            # print(f'Length : {len(sub_category_products_data)}')
            # print(f'Data: {sub_category_products_data}')

    def parse_product_by_page(self, page, sub_cat_name):
        data = dict()
        category = f'{self.__category_name} > {sub_cat_name}'
        data['Categories'] = category
        soup = BeautifulSoup(page, 'lxml')
        name = soup.find('div', class_='productfull__header-title').find('h1').text
        data['Name'] = name

        regular_price = str()
        sale_price = str()
        try:
            regular_price = soup.find('div', class_='productfull__pricebox-top').find('div',
                                                                                      class_='productfull__price-old').text[
                            :-2].strip().replace(' ', '')
            if int(regular_price) < 2000:
                return dict()
            sale_price = soup.find('div', class_='productfull__price').find('div',
                                                                            class_='productfull__price-new').text[
                         :-2].strip().replace(' ', '')
            data['In stock?'] = 1
        except AttributeError:
            in_stock = soup.find('span', class_='productfull__instock _none')
            if in_stock is not None:
                regular_price = None
                data['In stock?'] = 0
            else:
                regular_price = soup.find('div', class_='productfull__price').find('div',
                                                                                   class_='productfull__price-new').text[
                                :-2].strip().replace(' ', '')
                if int(regular_price) < 2000:
                    return dict()
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

    def parse_sub_categories_to_get_product_urls(self, sub_cat_url, sub_cat_url_clean):
        response = requests.get(sub_cat_url)
        print(f'Parsing sub categories!')
        soup = BeautifulSoup(response.text, 'lxml')
        final_urls = []
        urls = soup.find('div', class_='product-grid').find_all('div', class_='product-grid__item')
        for elem in urls:
            try:
                url = elem.find('div', class_='product-card__img').find('a').get('href')
                final_urls.append(self.__main_page + url)
            except AttributeError:
                continue
        pagination = soup.find('div', class_='pagination__pager').find_all('a', class_='pagination__page')
        url_to_greq = []
        for el in range(2, int(pagination[-1:][0].text) + 1):
            url = f'{self.__main_page}{sub_cat_url_clean}{el}.html'
            url_to_greq.append(url)
        resp_ = (grequests.get(url) for url in url_to_greq)
        grespones = grequests.map(resp_, size=15)
        for response_ in grespones:
            soup = BeautifulSoup(response_.text, 'lxml')
            urls = soup.find('div', class_='product-grid').find_all('div', class_='product-grid__item')
            for elem in urls:
                try:
                    url = elem.find('div', class_='product-card__img').find('a').get('href')
                    final_urls.append(self.__main_page + url)
                except AttributeError:
                    continue
        return final_urls


def main():
    # parser = Parser(category_url='samokaty', category_name='Самокаты')
    parser1 = Parser(category_url='veloekipirovka', category_name='Экипировка')
    # parser.parse()
    parser1.parse()


if __name__ == '__main__':
    main()

import json

import requests
from bs4 import BeautifulSoup

resp = requests.get(
    'https://kzn.velo-shop.ru/catalog/gornye/kolesa-27-5-novyy-standart/velosiped-adrenalin-md-27-5-v010-ciniy-18/')

soup = BeautifulSoup(resp.text, 'lxml')

scripts = soup.find_all('script')
count = 0
for script in scripts:
    if 'JCCatalogElement' in script.text:
        text_script = script.text.strip()
        json_ = text_script.split('new JCCatalogElement(')[1].strip()
        json_ = json_.split(');')[0].strip()
        json_ = json_.replace("'", '"')
        print(json_)
        jsonObj = json.loads(json_)
        print(jsonObj)
        slider = jsonObj['OFFERS'][0]['SLIDER']
        if len(slider) == 0:
            print(jsonObj['OFFERS'][0]['NO_PHOTO']['SRC'])
        else:
            for slide in slider:
                print(slide['SRC'])
    count += 1

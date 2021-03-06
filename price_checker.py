from bs4 import BeautifulSoup
import configparser
from datetime import datetime
import os
import pathlib
import requests
import smtplib
import sys
import time
from mongo_helpers import mongo


def get_abs_path():
    return str(pathlib.Path(__file__).parent.absolute())


def get_system_path_slash():
    return '\\' if sys.platform == 'win32' else '/'


def convert_path_slashes(path=str):
    return path.replace('/', get_system_path_slash())


def get_config():
    config = configparser.ConfigParser()
    config_path = '{abs}/{filepath}'.format(
        abs=get_abs_path(), filepath='email.config')
    config.read(convert_path_slashes(config_path))
    return config


def send_price_check_email(item):
    config = get_config()
    server = smtplib.SMTP(config.get('GMAIL', 'host'),
                          int(config.get('GMAIL', 'port')))
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(user=config.get('GMAIL', 'email'),
                 password=config.get('GMAIL', 'password'))

    server.sendmail(config.get('GMAIL', 'email'),
                    item['email'], item['msg'])
    server.quit()


def get_page_content(URL):
    if URL is not None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88Safari/537.36'}
        page = requests.get(URL, headers=headers)
        soup = BeautifulSoup(BeautifulSoup(
            page.content, 'html.parser').prettify(), 'html.parser')
        return soup


def find_wayfair_item_info(items):
    soup = get_page_content(items['url'])
    items['title'] = soup.findAll(
        "h1", {"class": "pl-Heading pl-Heading--pageTitle"})[0].get_text().strip()
    items['price'] = float(str(soup.findAll("div", {"class": "BasePriceBlock"})[
                           0].get_text().strip()).replace('$', ''))
    items['under_target'] = False
    return items


def products_to_price_check():
    db = mongo(database='mydbs', collection='price_checker')
    return db.query_match(column='seller', value='wayfair')


def update_target_price_of_item(item):
    db = mongo(database='mydbs', collection='price_checker')
    query = {"url": item['url']}
    new_values = {"$set": {"target": item['price']}}
    db.update(query, new_values)


def get_info_for_items():
    items = products_to_price_check()
    for item in items:
        if item['seller'] == 'wayfair':
            item.update(find_wayfair_item_info(item))
    return items


def price_checker():
    items = get_info_for_items()
    for item in items:
        if item['price'] < item['target']:
            item['subject'] = '{title} - price fell! Now ${price}'.format(
                title=item['title'], price=item['price'])
            item['body'] = 'Check this link - {url} \n Price below target from ${target} to ${current_price}'.format(
                url=item['url'], target=item['target'], current_price=item['price'])
            item['msg'] = 'Subject: {subject}\n\n{body}'.format(
                subject=item['subject'], body=item['body'])
            send_price_check_email(item)
            update_target_price_of_item(item)


if __name__ == '__main__':
    price_checker()

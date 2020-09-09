from bs4 import BeautifulSoup

from config import COMPANIES

import datetime
import logging
import decimal
import requests
import time
import csv

logging.basicConfig(level=logging.DEBUG)


def write_csv(filename, fieldnames, data):
    with open(filename, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def get_fin_data():
    for company in COMPANIES:
        url = f'https://query1.finance.yahoo.com/v7/finance/download/' \
              f'{company}?period1=0&period2={int(time.time())}&interval=1d&events=history'
        r = requests.get(url)
        data_lines = r.content.decode("utf-8").splitlines()

        fieldnames = data_lines[0].split(',')

        data = list()
        for row in data_lines[1:]:
            temp_dict = dict()
            for index, item in enumerate(row.split(',')):
                if fieldnames[index] == 'Date':
                    temp_dict[fieldnames[index]] = datetime.datetime.strptime(item, '%Y-%m-%d')
                else:
                    temp_dict[fieldnames[index]] = float(item)
            temp_dict['3day_before_change'] = '-'
            data.append(temp_dict)

        fieldnames.append('3day_before_change')
        for index, row in enumerate(data):
            three_days_ago = row['Date'] - datetime.timedelta(days=3)
            found = list(filter(lambda x: x['Date'] == three_days_ago, data))
            if found:
                row['3day_before_change'] = float(decimal.Decimal(row['Close']) / decimal.Decimal(found[0]['Close']))

        write_csv(filename=f'{company}.csv', fieldnames=fieldnames, data=data)

        logging.info(f'{company} finance data ready\n')


def get_news():
    base_url = 'https://finance.yahoo.com'

    for company in COMPANIES:
        news = []

        resp_news = requests.get(url=f'{base_url}/quote/{company}')
        soup = BeautifulSoup(resp_news.text, 'lxml')

        for item in soup.find("div", {"id": "quoteNewsStream-0-Stream"}).ul.find_all("li")[:10]:
            temp_dict = dict()
            link = item.a['href']
            if not link.startswith('http'):
                link = f"{base_url}/{link}"
            news_page_soup = BeautifulSoup(requests.get(url=f'{link}', allow_redirects=True).text, 'lxml')

            temp_dict['title'] = news_page_soup.find("h1").string
            temp_dict['link'] = base_url + link

            news.append(temp_dict)

        write_csv(filename=f'{company}_news.csv', fieldnames=['title', 'link'], data=news)
        logging.info(f'{company} news ready\n')


if __name__ == '__main__':
    get_fin_data()
    get_news()

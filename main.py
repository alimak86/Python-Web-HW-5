import platform
import sys
import aiohttp
import asyncio
import logging
import threading
from collections import UserDict

from datetime import datetime, timedelta

EUR = "EUR"
USD = "USD"
sale = "sale"
purchase = "purchase"
currency = "currency"
pb_sale = "saleRate"
pb_purchase = "purchaseRate"

URL = 'https://api.privatbank.ua/p24api/exchange_rates?date='
DAYS_LIMIT = 2

OUTPUT = []  # accumulate the results


class Date:

    def __init__(self, date: datetime):
        pass


class Currency(UserDict):

    def __init__(self, currency_list):
        self.data = {}
        # print(currency_list)
        for currency in currency_list:
            self.data[currency] = {
                sale: -1,
                purchase: -1
            }  # create empty dictionary


class ExchangeRate:  # responsible for the work under the rates for the defined date

    def __init__(self, date: datetime, rates):
        self.year, self.month, self.day = str(date.date()).split("-")
        self.rate = rates
        self.datestr = ".".join([self.day, self.month, self.year])
        # print(self.rate)

    def date(self):
        return self.datestr

    def __call__(self, barrier: threading.Barrier, date):
        logging.debug("is working")
        record = Currency([EUR, USD])
        found_eur = False
        found_usd = False
        # print(self.rate)
        for rate in self.rate:
            # print(rate[currency])
            if rate[currency] == EUR:
                record[EUR][sale] = rate[pb_sale]
                record[EUR][purchase] = rate[pb_purchase]
                found_eur = True
                # print("found EUR")

            if rate[currency] == USD:
                record[USD][sale] = rate[pb_sale]
                record[USD][purchase] = rate[pb_purchase]
                found_usd = True
                # print("found USD")

            if found_eur and found_usd:
                # print(record)
                # return record
                OUTPUT.append({date: record})
                barrier.wait()
                break
        return {}


# class Client:  ## responsible for the communication with server
# DOES NOT WORK

#   async def __init__(self, url: str):
#     self.url = url
#     self.session = aiohttp.ClientSession()

#   async def ask_server(self):
#     try:
#       response = self.session.get(self.url)
#       if response.status == 200:
#         result = await response.json()
#         return result
#       else:
#         print(f"Error status: {response.status} for {url}")
#     except aiohttp.ClientConnectorError as err:
#       print(f'Connection error: {url}', str(err))


async def main(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    print(f"Error status: {response.status} for {url}")
        except aiohttp.ClientConnectorError as err:
            print(f'Connection error: {url}', str(err))


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG,
                        format='%(threadName)s %(message)s')

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    output = []
    days_to_check = int(sys.argv[1])

    if days_to_check > DAYS_LIMIT:
        limit = DAYS_LIMIT
    else:
        limit = days_to_check

    barrier = threading.Barrier(limit + 1)  # includeing main thread
    current_date = datetime.now()

    print(f"Will process the data for no more than {DAYS_LIMIT} days\n")

    for day in range(days_to_check):
        if day < DAYS_LIMIT:
            calculated_date = current_date - timedelta(days=day)
            year, month, day = str(calculated_date.date()).split("-")
            date = ".".join([day, month, year])

            url = URL + date  # generate API fro the current date

            r = asyncio.run(main(url))
            rates = r["exchangeRate"]
            rate = ExchangeRate(calculated_date, rates)
            thread = threading.Thread(
                target=rate, args=(barrier, date), name=date)
            thread.start()

            # output.append({rate.date(): rate.__call__()})
    current = barrier.wait()
    print("\nCurrently we have the following:\n")
    print(OUTPUT)

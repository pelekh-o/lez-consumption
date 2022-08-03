from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from os import environ

import google_sheets_service as gsheet_service

URL = 'https://my.lez.com.ua'
GSH_FILE = 'electricity_bills'
GSH_WSH_CONSUMPTION = 'Consumption'
GSH_WSH_BILL = 'Billing'
TIMEDELTA_DAYS = 20


def parse_billing_account_url(driver):
    # Get link to the billing account nuber
    # Currently implemented only for one billing account,
    # but it is possible to have multiple billing accounts for one user
    # Will make it in the futures updates
    element = driver.find_element(By.XPATH, '//*[@id="top"]/div/div/main/div/div/div[2]/div[2]/table/tbody/tr/td[1]/a')
    billing_account = element.get_attribute("href")
    billing_account = billing_account.replace('/DetailsSaldo', '')
    return billing_account


def parse_consumption(driver, billing_account_url):
    period = (datetime.today() - timedelta(days=TIMEDELTA_DAYS)).strftime('%Y%m')

    consumption_url = f'{billing_account_url}/ConsumptionOrders/consumption?periodFrom={period}&periodTo={period}'
    driver.get(consumption_url)

    table_id = driver.find_element(By.TAG_NAME, 'table')
    rows = table_id.find_elements(By.TAG_NAME, 'tr')  # get all the rows in the table

    # Get table rows with consumption details
    for row in range(1, len(rows)):
        r = table_id.find_elements(By.XPATH, f'//body//tbody//tr[{str(row)}]')
        for row_data in r:
            col = row_data.find_elements(By.TAG_NAME, 'td')
            date = translate_month(col[0].text)
            consumption = col[1].text
            gsheet_service.upload_row([date, consumption], GSH_FILE, GSH_WSH_CONSUMPTION)


def parse_billing(driver, billing_account_url):
    period = (datetime.today() - timedelta(days=TIMEDELTA_DAYS)).strftime('%Y%m')

    billing_url = f'{billing_account_url}/Payments?periodFrom={period}&periodTo={period}'
    driver.get(billing_url)

    table_id = driver.find_element(By.TAG_NAME, 'table')
    rows = table_id.find_elements(By.TAG_NAME, 'tr')  # get all the rows in the table
    # Get table rows with billing details
    for row in range(1, len(rows)):
        r = table_id.find_elements(By.XPATH, f'//body//tbody//tr[{str(row)}]')
        for row_data in r:
            col = row_data.find_elements(By.TAG_NAME, 'td')
            date = convert_billing_period(col[1].text)
            bill = col[2].text
            gsheet_service.upload_row([date, bill], GSH_FILE, GSH_WSH_BILL)


def convert_billing_period(str_date):
    date = str_date.split('.')
    date_m, date_y = int(date[0]), int(date[1])
    # The portal shows the date when the bill was paid,
    # although in fact the previous month is paid in the current month
    # (i.e. when it says 07.2022 - UAH 500, it means that UAH 500 was paid in July for June)
    if date_m == 1:
        date_m = 12
        date_y -= 1
    else:
        date_m -= 1

    date = f'{date_m}/{date_y}'
    return date


def login(driver):
    driver.find_element(By.ID, 'Email').send_keys(environ.get('LEZ_EMAIL'))
    driver.find_element(By.ID, 'Password').send_keys(environ.get('LEZ_PASS'))
    driver.find_element(By.XPATH, '//*[@id="top"]/div/div/div/form/button').click()
    return driver


def translate_month(date):
    month_ua, year = date.split(' ')
    dates = {
        'Січень': 'January',
        'Лютий': 'February',
        'Березень': 'March',
        'Квітень': 'April',
        'Травень': 'May',
        'Червень': 'June',
        'Липень': 'July',
        'Серпень': 'August',
        'Вересень': 'September',
        'Жовтень': 'October',
        'Листопад': 'November',
        'Грудень': 'December'
    }
    return f'{dates[month_ua]} {year}'


def main():
    driver = webdriver.Chrome('./chromedriver')
    driver.get(URL)

    login(driver)
    billing_account = parse_billing_account_url(driver)

    parse_consumption(driver, billing_account)
    parse_billing(driver, billing_account)

    driver.close()


if __name__ == '__main__':
    main()

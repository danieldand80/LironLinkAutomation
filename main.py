import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import os
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1KCgCeP9gLHEPO4EP11nWKsjMwTCheXfZ8Jr_B7jE02E'

def get_sheets_client():
    # Проверяем env переменную с credentials
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    return gspread.authorize(creds)

def check_url_active(driver, url):
    """Проверяет активность URL по наличию элементов на странице"""
    if not url or url.strip() == '':
        return False
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        
        # Проверяем наличие типичных элементов товара
        selectors = [
            "//meta[@property='og:price:amount']",
            "//span[contains(@class, 'price')]",
            "//div[contains(@class, 'price')]",
            "//*[contains(@class, 'product-price')]",
            "//h1[contains(@class, 'product')]",
            "//h1[contains(@class, 'title')]",
        ]
        
        for selector in selectors:
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                return True
            except TimeoutException:
                continue
        
        # Если ни один элемент не найден, проверяем что мы не на главной странице
        current_url = driver.current_url
        if 'hamozot.com/products/' not in current_url:
            return False
            
        return False
    except (WebDriverException, Exception) as e:
        print(f"Ошибка проверки {url}: {e}")
        return False

def main():
    # Получаем стартовую строку из env или input
    start_row_env = os.getenv('START_ROW')
    if start_row_env:
        start_row = int(start_row_env)
        print(f"Запуск с строки {start_row} (из env)...")
    else:
        start_row = input("С какой строки начать? (по умолчанию 2): ").strip()
        start_row = int(start_row) if start_row else 2
        print(f"Запуск с строки {start_row}...")
    
    # Инициализация Google Sheets
    client = get_sheets_client()
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    
    # Получаем все данные
    all_values = sheet.get_all_values()
    
    # Находим индекс столбца URL и Status
    headers = all_values[0] if all_values else []
    url_col_idx = None
    status_col_idx = None
    
    for idx, header in enumerate(headers):
        if 'url' in header.lower() or 'link' in header.lower():
            url_col_idx = idx
        if 'status' in header.lower():
            status_col_idx = idx
    
    if url_col_idx is None:
        print("Не найден столбец с URL!")
        return
    
    if status_col_idx is None:
        print("Не найден столбец Status!")
        return
    
    # Настройка Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    
    try:
        # Проходим по строкам начиная с start_row
        for row_idx in range(start_row - 1, len(all_values)):
            row = all_values[row_idx]
            row_num = row_idx + 1
            
            # Получаем URL из строки
            url = row[url_col_idx] if url_col_idx < len(row) else ''
            
            print(f"Проверка строки {row_num}: {url}")
            
            # Проверяем активность
            if not url or url.strip() == '':
                status = 'not active'
            else:
                is_active = check_url_active(driver, url)
                status = 'active' if is_active else 'not active'
            
            # Обновляем статус в таблице
            status_cell = f"{chr(65 + status_col_idx)}{row_num}"
            sheet.update(status_cell, status)
            print(f"  → {status}")
            
            time.sleep(1)  # Пауза между запросами
    
    finally:
        driver.quit()
    
    print("Готово!")

if __name__ == '__main__':
    main()

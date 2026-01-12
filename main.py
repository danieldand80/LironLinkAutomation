import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
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

def check_url_active(driver, url, log_fn=print):
    """Проверяет активность URL по наличию элементов на странице"""
    if not url or url.strip() == '':
        return False
    
    try:
        driver.get(url)
        time.sleep(2)  # Ждем загрузки страницы
        
        # Проверяем редирект на главную или 404
        current_url = driver.current_url
        if 'hamozot.com/products/' not in current_url:
            log_fn(f"  Редирект на: {current_url}")
            return False
        
        # Проверяем наличие 404 текста
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            if 'עמוד לא נמצא' in page_text or '404' in page_text:
                log_fn(f"  Найден 404")
                return False
        except:
            pass
        
        wait = WebDriverWait(driver, 5)
        
        # Проверяем типичные элементы товара
        selectors = [
            "//meta[@property='og:price:amount']",
            "//span[contains(@class, 'price')]",
            "//div[contains(@class, 'price')]",
            "//*[contains(text(), '₪')]",  # Проверка символа шекеля
            "//h1",  # Любой заголовок H1
            "//*[contains(@class, 'product')]",
        ]
        
        for selector in selectors:
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                log_fn(f"  Найден элемент: {selector[:50]}")
                return True
            except TimeoutException:
                continue
        
        log_fn(f"  Элементы товара не найдены")
        return False
        
    except (WebDriverException, Exception) as e:
        log_fn(f"  Ошибка: {e}")
        return False

def run_check(start_row=2, log_fn=print):
    log_fn(f"Запуск с строки {start_row}...")
    
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
        log_fn("Не найден столбец с URL!")
        return
    
    if status_col_idx is None:
        log_fn("Не найден столбец Status!")
        return
    
    # Настройка Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.binary_location = '/usr/bin/chromium'
    
    # На Railway используем системный chromedriver
    if os.path.exists('/usr/bin/chromedriver'):
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
    else:
        # Локально используем webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Проходим по строкам начиная с start_row
        for row_idx in range(start_row - 1, len(all_values)):
            row = all_values[row_idx]
            row_num = row_idx + 1
            
            # Получаем URL из строки
            url = row[url_col_idx] if url_col_idx < len(row) else ''
            
            log_fn(f"Проверка строки {row_num}: {url}")
            
            # Проверяем активность
            if not url or url.strip() == '':
                status = 'not active'
            else:
                is_active = check_url_active(driver, url, log_fn)
                status = 'active' if is_active else 'not active'
            
            # Обновляем статус в таблице
            status_cell = f"{chr(65 + status_col_idx)}{row_num}"
            sheet.update(status_cell, status)
            log_fn(f"  → {status}")
            
            time.sleep(1)  # Пауза между запросами
    
    finally:
        driver.quit()
    
    log_fn("Готово!")

if __name__ == '__main__':
    start_row = int(os.getenv('START_ROW', '2'))
    run_check(start_row)

# Liron Link Automation

Автоматическая проверка активности ссылок в Google Sheets.

## Установка

1. Установить зависимости:
```bash
pip install -r requirements.txt
```

2. Установить ChromeDriver:
   - Скачать с https://chromedriver.chromium.org/
   - Добавить в PATH

3. Настроить Google Sheets API:
   - Создать проект в Google Cloud Console
   - Включить Google Sheets API
   - Создать Service Account
   - Скачать credentials.json в корень проекта
   - Дать доступ к таблице для email из credentials.json

## Использование

Локально:
```bash
python main.py
```

Программа спросит с какой строки начать (по умолчанию 2).

## Деплой на Railway

1. Подключи GitHub репозиторий к Railway
2. В настройках Deploy Commands:
   - Build: `pip install -r requirements.txt`
   - Start: `python main.py`
3. В Settings → Nixpacks добавь в apt packages: `chromium chromium-driver`
4. Переменные окружения:
   - `GOOGLE_CREDENTIALS_JSON` - содержимое credentials.json (весь JSON как строка)
   - `START_ROW` - стартовая строка (по умолчанию 2)

## Как работает

1. Читает URL из Google Sheets
2. Открывает каждую ссылку через Selenium
3. Проверяет наличие элементов товара (цена, заголовок)
4. Обновляет статус: "active" или "not active"
5. Пустые строки получают статус "not active"
6. При перезапуске старые статусы перезаписываются

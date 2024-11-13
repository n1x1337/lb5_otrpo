### Пример переменных окружения в .env.example

## Запуск

```bash
git clone https://github.com/n1x1337/lb5_otrpo
cd lb5_otrpo
pip install -r requirements.txt
uvicorn main:app
```

API будет доступен по адресу: `http://127.0.0.1:8000`.

## Тесты

Чтобы запустить тесты введите команду 

```bash
pytest tests/test_main.py
```
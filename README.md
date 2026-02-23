# AI-TestTask
Test Task for int20h hackathon 2026 in AI category

# Запуск проєкту
1. **Налаштуйте змінні середовища:**
    Перейменуйте `.env.example` в `.env` та вставте власний ключ.
2. **Запустіть Docker-середовище:**
   Проєкт використовує volume-маунтинг, тому всі зміни в коді та згенеровані дані миттєво синхронізуються з вашою локальною файловою системою.
   При додаванні нових бібліотек також використовуйте цю команду.
```bash
docker-compose up -d --build
```

# Запуск проєкту
Має 2 ендпоінти: 
 - generator (Генерує dataset: розмови клієнта та support-агента)
 - analyzer (Аналізує роботу support-агента, та видає результат в json)

### Generator:
```bash
docker-compose exec app python generator.py
```

### Analyzer:

```bash
docker-compose exec app python analyzer.py
```
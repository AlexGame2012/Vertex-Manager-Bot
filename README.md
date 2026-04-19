# ⚡ Vertex — Telegram Чат-Менеджер

**Vertex** — мощный и современный чат-менеджер для Telegram с продвинутой модерацией, экономикой, подарками и азартными играми. Бот автоматизирует управление чатом, помогая администраторам поддерживать порядок и вовлекать участников.

[![GitHub release](https://img.shields.io/badge/version-1.0.2-blue.svg)](https://github.com/AlexGame2012/Vertex-Manager-Bot)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/telegram-bot-blue.svg)](https://t.me/vertex_demo_bot)

---

## 📖 О проекте

Vertex создан для сообществ, которым нужен надёжный инструмент модерации без потери гибкости. Бот не только наказывает нарушителей, но и поощряет активность через игровые механики.

### 🎯 Основные возможности

| Категория | Возможности |
|-----------|-------------|
| 🛡️ **Модерация** | 5 уровней модераторов, баны, муты, кики, система предупреждений |
| 💰 **Экономика** | Внутренняя валюта «Вертексы», ферма, переводы между пользователями |
| ⭐ **Пополнение** | Покупка Вертексов за Telegram Stars (в ЛС бота) |
| 🎁 **Подарки** | Цветы, торты, мишки, кристаллы, трофеи — всё в профиле |
| 🎰 **Азартные игры** | Казино с множителями x1.5–x5, лутбоксы с редкими призами |
| 📊 **Статистика** | Активность пользователей, топ по валюте |
| 👤 **Профили** | Ники, звания, описание «о себе» |

---

## 🚀 Быстрый старт

### Добавление бота в чат

1. Напишите боту которого вы запустили
2. Нажмите «Добавить в чат»
3. Выдайте боту права администратора

### Основные команды

```bash
!ферма           # Заработать Вертексы
!вертексы        # Проверить баланс
!купить 100      # Пополнить баланс (Telegram Stars)
!профиль         # Посмотреть профиль
!магазин         # Список подарков
!подарить @user  # Подарить подарок другу
!казино 100      # Сыграть в казино
!лутбокс         # Открыть лутбокс (150 VTS)
```

> 📌 **Префиксы команд:** `!` `.` `/` `Vertex ` `Вертекс `

---

## 🛠️ Установка и запуск

### Требования

- Python 3.11+
- pip

### Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/AlexGame2012/Vertex-bot.git
cd Vertex-bot

# Установите зависимости
pip install -r requirements.txt
```

### Настройка

Создайте файл `config.py`:

```python
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"
PREFIXES = ['!', '.', '/', 'Vertex ', 'Вертекс ']
RANKS = {0: "участник", 1: "младший модератор", 2: "старший модератор", 
         3: "администратор", 4: "старший администратор", 5: "создатель"}
MASTER_ID = 123456789  # Ваш Telegram ID
CURRENCY_NAME = "Вертексы"
CURRENCY_EMOJI = "⚡"
STARS_TO_VERTEX_RATE = 5  # 1 Star = 5 Вертексов
```

### Запуск

```bash
cd src
python main.py
```

---

## 📁 Структура проекта

```
Vertex-bot/
├── src/
│   ├── main.py          # Основной код бота
│   ├── logic.py         # Работа с базой данных
│   ├── config.py        # Конфигурация (токен, префиксы, ранги)
│   └── requirements.txt # Зависимости
├── vertex_bot.db        # База данных SQLite (создаётся автоматически)
└── README.md            # Документация
```

---

## 💰 Пополнение баланса

Пользователи могут пополнить баланс Вертексов через **Telegram Stars**:

- Команда `!купить 100` — покупка в ЛС бота
- 1 Star = 5 Вертексов
- Минимальная покупка — 10 Stars
- Мгновенное зачисление после оплаты

---

## 📄 Лицензия

Проект распространяется под лицензией MIT.

---

## 👨‍💻 Разработчик

**AlexStudio Code**

- 🌐 Сайт: [alexstudiocode.ru](https://alexstudiocode.ru)
- 📧 Почта: [info@alexstudiocode.ru](mailto:info@alexstudiocode.ru)
- 🆘 Поддержка: [support@alexstudiocode.ru](mailto:support@alexstudiocode.ru)
- 🐙 GitHub: [AlexGame2012](https://github.com/AlexGame2012)

---

## 🔗 Ссылки

- 📖 **Документация**: [alexstudiocode.ru/project/Vertex](https://alexstudiocode.ru/project/Vertex)
- 🆘 **Поддержка**: [support@alexstudiocode.ru](mailto:support@alexstudiocode.ru)
- 🐙 **GitHub**: [AlexGame2012/Vertex-Manager-Bot](https://github.com/AlexGame2012/Vertex-Manager-Bot)

---

## ⭐ Поддержка проекта

Если вам нравится Vertex, поставьте звезду на GitHub — это помогает проекту развиваться!

[![GitHub stars](https://img.shields.io/github/stars/AlexGame2012/Vertex-Manager-Bot?style=social)](https://github.com/AlexGame2012/Vertex-Manager-Bot)

---

© 2026 AlexStudio Code. All rights reserved.

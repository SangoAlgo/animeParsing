# 🎌 AnimeParsing — Anime Catalog, Database & Online Player

[![Deploy on Render](https://img.shields.io/badge/Deploy%20to-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![Deploy on Railway](https://img.shields.io/badge/Deploy%20to-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](#-запуск-через-docker)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)

Полнофункциональная платформа для агрегации, поиска, фильтрации и онлайн-просмотра аниме с агрегацией метаданных из множества источников (**Shikimori, AniList, Kodik, AnimeGo, AnimeThemes, Manga, Sakuga, Aniskip**).

---

## 🌟 Основные возможности

- ⚡ **SQLite FTS5 Full-Text Search**: Мгновенный полнотекстовый поиск по русским, английским, японским названиям, синонимам и описаниям.
- 🎯 **Мультифасетная фильтрация**: Фильтры по жанрам, студиям, озвучкам (Kodik), форматам (TV, Movie, OVA...), статусам, годам и рейтингам.
- 🎬 **JIT Kodik Stream Resolver**: Встроенный онлайн-плеер на базе **HLS.js** с разрешением `.m3u8` потоков на лету, выбором озвучек, качества и серий.
- ⏩ **Автоматический пропуск опенингов и филлеров**: Интеграция с **AniSkip API** (таймкоды опенингов/эндингов) и базой филлеров.
- 📦 **База данных 2200+ тайтлов**: Автоматическая распаковка SQLite базы данных из сжатых фрагментов без внешних зависимостей.
- 🎨 **Эстетичный интерфейс**: React 19 + Vite с плавной анимацией, карточками, фильтрами и полноэкранным плеером.

---

## 🚀 Как запустить онлайн бесплатно

### Вариант 1. Render.com (Рекомендуется, 1 клик)
1. Зарегистрируйтесь на [Render.com](https://render.com).
2. Нажмите **New +** ➔ **Web Service**.
3. Подключите ваш GitHub репозиторий: `https://github.com/SangoAlgo/animeParsing`.
4. Выберите **Docker** в качестве Environment (Render автоматически подхватит `Dockerfile`).
5. Нажмите **Create Web Service** — проект соберется и запустится с постоянным HTTPS адресом!

---

### Вариант 2. Railway.app
1. Зарегистрируйтесь на [Railway.app](https://railway.app).
2. Нажмите **New Project** ➔ **Deploy from GitHub repo** ➔ выберите `animeParsing`.
3. Railway автоматически распознает `railway.json` / `Dockerfile` и запустит сервис.

---

### Вариант 3. Hugging Face Spaces (Бесплатно 24/7)
1. Создайте Space на [Hugging Face Spaces](https://huggingface.co/spaces).
2. Выберите тип **Docker**.
3. Подключите или скопируйте файлы репозитория. Приложение сразу станет доступно онлайн.

---

### Вариант 4. Запуск через Docker на своем сервере / VPS

```bash
# Клонируйте репозиторий
git clone https://github.com/SangoAlgo/animeParsing.git
cd animeParsing

# Сборка и запуск контейнера
docker-compose up --build -d
```
Приложение откроется на `http://localhost:8000`.

---

## 💻 Локальный запуск и разработка

### Требования
- **Python 3.10+**
- **Node.js 18+** и **npm**

### 1. Установка зависимостей

```bash
# Установка зависимостей backend
pip install -r backend/requirements.txt

# Установка зависимостей frontend
cd frontend
npm install
cd ..
```

### 2. Запуск сервера и интерфейса

#### Режим разработки (с Hot-Reload):
```bash
# Терминал 1: Запуск API бэкенда
python backend/server.py 8000

# Терминал 2: Запуск Vite дев-сервера
cd frontend
npm run dev
```
Откройте в браузере: `http://localhost:5173`.

#### Продакшн режим:
```bash
# 1. Сборка фронтенда
cd frontend
npm run build
cd ..

# 2. Запуск единого сервера (раздает и API, и фронтенд)
python backend/server.py 8000
```
Откройте в браузере: `http://localhost:8000`.

---

## 📡 Спецификация API

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/titles` | Поиск, фильтрация (жанры, студии, озвучки, года) и пагинация |
| `GET` | `/api/title/<key>` | Полное досье тайтла (эпизоды, озвучки, связанные тайтлы, манга, темы) |
| `GET` | `/api/filters` | Список фасетов для фильтров (топ жанров, студий, озвучек, диапазон лет) |
| `GET` | `/api/catalog/<shikimori_id>` | Каталог озвучек и серий Kodik для тайтла |
| `GET` | `/api/resolve?link=<url>` | JIT стрим-резолвер (`.m3u8` ссылка потока + таймкоды AniSkip) |
| `GET` | `/api/health` | Проверка работоспособности сервера |

---

## 📁 Структура проекта

```text
AnimeParsing/
├── backend/                  # Python бэкенд и сборщики данных
│   ├── collectors/           # Парсеры: Shikimori, AniList, Kodik, AnimeThemes, Manga и др.
│   ├── scripts/              # Миграции и подготовка базы данных
│   ├── db.py                 # SQLite слой с FTS5 поиском и реляционными связями
│   ├── kodik.py              # Парсинг и стриминг Kodik
│   ├── server.py             # HTTP сервер API и раздача статики
│   └── requirements.txt      # Python зависимости
├── frontend/                 # React 19 + Vite интерфейс
│   ├── src/
│   │   ├── components/       # Компоненты UI (Плеер, Карточки, Досье, Поиск)
│   │   ├── App.jsx           # Главный компонент и роутинг
│   │   └── index.css         # Стилизация и дизайн-система
│   └── package.json          # Node.js зависимости
├── data/                     # База данных тайтлов и кэши
│   ├── anime.db.gz.00        # Сжатые фрагменты SQLite базы (авто-распаковка)
│   ├── anime.db.gz.01
│   ├── aniskip_cache.json    # Кэш таймкодов опенингов
│   └── fillers_cache.json    # Кэш списков филлеров
├── Dockerfile                # Multi-stage production сборка
├── docker-compose.yml        # Docker Compose конфиг
├── render.yaml               # Конфиг 1-Click деплоя на Render
├── railway.json              # Конфиг деплоя на Railway
└── README.md
```

---

## 📄 Лицензия

MIT License.

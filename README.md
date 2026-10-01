# My Choice API

Бэкенд платформы интерактивных визуальных новелл: пользователь описывает идею, по ней генерируется сюжет новеллы с ветвлениями, персонажами и диалогами.

Сам сервис сюжет не генерирует. Он принимает HTTP-запросы и отправляет задачи на генерацию в Kafka. Обрабатывает их отдельный сервис `ai_plot`.

```
Клиент ──HTTP──▶ my_choice_api ──Kafka: ai_plot.novel.generate──▶ ai_plot
```

## Стек

- Python 3.13, FastAPI, Uvicorn
- PostgreSQL 18, SQLAlchemy 2, Alembic
- Kafka 3.8 (KRaft, без ZooKeeper), aiokafka
- uv для управления зависимостями
- Docker Compose и Traefik для локального запуска

## Структура

Проект построен по гексагональной архитектуре (ports & adapters):

```
src/
├── core/            # доменная логика: модели, сервисы, протоколы (порты)
├── inbound/         # входящие адаптеры
│   ├── http/        #   FastAPI-роутеры
│   └── kafka/       #   Kafka consumer
├── outbound/        # исходящие адаптеры
│   ├── ai_plot/     #   шлюз к сервису генерации сюжета
│   ├── kafka/       #   Kafka producer
│   └── database/    #   SQLAlchemy, миграции Alembic
└── main/            # точка входа и конфигурация
```

## Запуск

### Что нужно заранее

- Docker и Docker Compose
- make
- Запущенный [Traefik](https://doc.traefik.io/traefik/) во внешней Docker-сети `traefik`. Через него открываются API и Kafka UI. Если сети ещё нет, создайте её:

  ```bash
  docker network create traefik
  ```

### 1. Секреты

Создайте в корне проекта файл `.secrets` с параметрами PostgreSQL. Он не коммитится.

```dotenv
# Postgres
POSTGRES__DB=my_choice
POSTGRES__HOST=db_pg
POSTGRES__PORT=5432
POSTGRES__USER=my_choice
POSTGRES__PASSWORD=change_me
```

Остальные переменные лежат в [env.example](env.example). При каждом запуске `make` склеивает `env.example` и `.secrets` в `.env`. Сам `.env` руками не редактируйте: он перезаписывается.

### 2. Старт

```bash
make upd
```

Команда соберёт образ и поднимет PostgreSQL, Kafka, Kafka UI и приложение. Перед стартом приложение применяет миграции (`alembic upgrade head`). Одноразовый контейнер `kafka-init` создаёт топики из [scripts/kafka/init-topics.sh](scripts/kafka/init-topics.sh).

### 3. Проверка

| Что | Адрес |
|---|---|
| Swagger UI | http://my_choice.localhost/docs |
| Health check | http://my_choice.localhost/health |
| Kafka UI | http://kafka.localhost |
| PostgreSQL с хоста | `localhost:9876` |

Пример запроса на генерацию новеллы:

```bash
curl -X POST http://my_choice.localhost/novels/ \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "Детектив в киберпанк-городе", "universe_id": 1}'
```

При успехе возвращается `204`, а сообщение появляется в топике `ai_plot.novel.generate`. Его можно посмотреть в Kafka UI.

## Команды make

| Команда | Описание |
|---|---|
| `make upd` | Собрать и запустить в фоне (с пересозданием контейнеров) |
| `make up` | То же, но с логами в терминале |
| `make just_up` | Запустить без пересборки |
| `make start` / `make stop` | Запустить или остановить существующие контейнеры |
| `make restart` | Перезапустить контейнеры |
| `make down` | Остановить и удалить контейнеры |
| `make migration m="Описание"` | Сгенерировать миграцию Alembic (контейнер `app` должен быть запущен) |
| `make prune` | Очистить неиспользуемые Docker-ресурсы (с подтверждением) |

## Конфигурация

Настройки читаются из `.env` через pydantic-settings. Вложенные поля разделяются `__`.

| Переменная | По умолчанию | Описание |
|---|---|---|
| `APP__LOGGING_LEVEL` | `DEBUG` | Уровень логирования |
| `APP__DEBUG_MODE` | `false` | Режим отладки |
| `APP__ROOT_PATH` | `/` | Root path для работы за прокси |
| `KAFKA__BOOTSTRAP_SERVERS` | `kafka:9092` | Адрес брокера Kafka |
| `KAFKA__CLIENT_ID` | `my-choice-api` | Client ID продюсера |
| `POSTGRES__DB`, `__HOST`, `__PORT`, `__USER`, `__PASSWORD` | — | Подключение к PostgreSQL (обязательные) |

## Kafka-топики

| Топик | Направление | Назначение |
|---|---|---|
| `ai_plot.novel.generate` | публикуем | Запрос на генерацию новеллы: `request_id`, `prompt`, `universe_id` |

Новые топики добавляются в массив `TOPICS` в [scripts/kafka/init-topics.sh](scripts/kafka/init-topics.sh).

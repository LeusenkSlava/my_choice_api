# My Choice API

Бэкенд платформы интерактивных визуальных новелл: пользователь описывает идею, по ней генерируется сюжет новеллы с ветвлениями, персонажами и диалогами.

Сам сервис сюжет не генерирует и новеллы не хранит. Он работает прослойкой между клиентом и сервисом `ai_plot`, а взаимодействие идёт двумя путями:

- **Чтение (синхронно, HTTP).** Карточка и список новелл, удаление и следующая реплика проксируются в HTTP API `ai_plot` с коротким таймаутом.
- **Генерация (асинхронно, Kafka).** Генерация новеллы или следующей сцены занимает десятки секунд, поэтому HTTP-запрос её не ждёт. Сервис сохраняет задачу (`GenerationJob`) в PostgreSQL и сразу отвечает клиенту `202` с `id` задачи. Затем фоновый воркер отправляет задачу в Kafka (паттерн Transactional Outbox), а результат приходит обратно через Kafka.

```
Клиент ──HTTP──▶ my_choice_api ──HTTP (чтение)──▶ ai_plot
                     │
                     └──INSERT──▶ generation_jobs (PostgreSQL)
                                        │
             relay-воркер ◀─────────────┘
                  │
                  ├──Kafka: ai_plot.novel.generate──▶ ai_plot
                  └──Kafka: ai_plot.scene.generate──▶ ai_plot
                                                        │
   consume_loop ◀──Kafka: generation.results────────────┘
        │
        └──▶ generation_jobs: статус done / failed
```

Как пользоваться API из клиентского приложения, описано в [docs/client-api.md](docs/client-api.md).

### Чтение новеллы и генерация сцен

`GET /novels/{id}/next?offset=` запрашивает у `ai_plot` следующую реплику. Возможны три исхода:

- реплика готова: сервис отдаёт её (`200 ok`);
- новелла пройдена: `200 finished`;
- сцена ещё не сгенерирована: сервис создаёт задачу типа `scene` и отвечает `202 generating` с `id` задачи.

**Заранее запускаемая генерация.** Когда сервис отдаёт последнюю реплику сцены, а новелла ещё не закончилась, он сразу проверяет, готова ли следующая сцена. Если нет, ставит задачу на её генерацию. Пока пользователь читает последнюю реплику, сцена генерируется, так что `202` возникает редко.

### Жизненный цикл задачи

| Статус | Что значит |
|---|---|
| `created` | Задача сохранена и ждёт отправки |
| `publishing` | Relay-воркер забрал задачу (`SELECT … FOR UPDATE SKIP LOCKED`) и отправляет её |
| `sent` | Задача отправлена в Kafka, ждём результата от `ai_plot` |
| `done` | Генерация прошла успешно, в задаче записан `result_id` |
| `failed` | Генерация завершилась ошибкой, текст лежит в `error` |

Если отправить в Kafka не удалось, задача возвращается в `created`, и воркер попробует снова.

**Типы задач** (`kind`): `novel` для генерации новеллы и `scene` для генерации следующей сцены. В `result_id` записывается id новеллы или сцены соответственно.

**Дедупликация.** У каждой задачи есть `dedup_key`:

- `novel`: sha256 от нормализованного `prompt` (без лишних пробелов, в нижнем регистре) и `universe_id`;
- `scene`: `"{novel_id}:{scene_order}"`.

Пока есть активная задача (`created`, `publishing` или `sent`) того же типа с таким же ключом, повторный запрос вернёт её, а не создаст новую. Гонки между параллельными запросами закрывает уникальное ограничение `uq_active_job` в БД.

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
│       ├── handlers/ #    обработчики сообщений по топикам (TOPIC_HANDLERS)
│       └── tasks/    #    consume_loop
├── outbound/        # исходящие адаптеры
│   ├── ai_plot/     #   HTTP-клиент, провайдер новелл, топики и relay-воркер
│   ├── kafka/       #   Kafka producer и publishers
│   └── database/    #   SQLAlchemy-модели, репозитории, миграции Alembic
└── main/            # точка входа, конфигурация, фоновые воркеры
```

Фоновые воркеры перечислены в `lifespan` в [src/main/run.py](src/main/run.py). Там же создаются Kafka-продюсер, консьюмер и HTTP-клиент `ai_plot`. При старте приложения их запускает `BackgroundTaskRunner` из [src/main/setup/background_tasks.py](src/main/setup/background_tasks.py), а при остановке корректно завершает:

- `generation_job_relay` раз в секунду забирает до 10 задач в статусе `created` и отправляет их в Kafka. Топик выбирается по типу задачи;
- `consume_loop` подписан на все топики из `TOPIC_HANDLERS` и передаёт каждое сообщение обработчику его топика. Если обработчик падает, сообщение повторяется с экспоненциальной задержкой (от 1 до 30 с). Offset коммитится вручную только после успешной обработки (`enable_auto_commit=False`), то есть сообщения доставляются по схеме at-least-once. Сообщения, которые не проходят валидацию, пропускаются.

## Запуск

### Что нужно заранее

- Docker и Docker Compose
- make
- Запущенный сервис `ai_plot`, доступный по `AI_PLOT__BASE_URL`. Без него ручки чтения новелл отвечают `502`
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

Ответ `202 Accepted` содержит идентификатор и статус задачи:

```json
{"id": 1, "status": "created"}
```

Примерно через секунду relay-воркер отправит задачу в топик `ai_plot.novel.generate` (это видно в Kafka UI), и её статус сменится на `sent`. Повторный такой же запрос, пока задача активна, вернёт тот же `id`. Статус задачи можно посмотреть так:

```bash
curl http://my_choice.localhost/generation-jobs/1
```

Чтение новеллы с начала:

```bash
curl http://my_choice.localhost/novels/1/next
```

### HTTP API

| Метод и путь | Назначение |
|---|---|
| `POST /novels/` | Запустить генерацию новеллы → `202` + задача |
| `GET /novels/?limit=&offset=` | Список новелл |
| `GET /novels/{id}` | Карточка новеллы |
| `DELETE /novels/{id}` | Удалить новеллу |
| `GET /novels/{id}/next?offset=` | Следующая реплика: `200 ok`, `200 finished` или `202 generating` + задача |
| `GET /generation-jobs/{id}` | Статус задачи генерации |
| `GET /health` | Health check |

Подробно, с примерами и сценариями для клиента: [docs/client-api.md](docs/client-api.md).

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
| `AI_PLOT__BASE_URL` | `http://ai_plot:8000` | Адрес HTTP API сервиса `ai_plot` |
| `AI_PLOT__TIMEOUT` | `10` | Таймаут HTTP-запросов к `ai_plot`, в секундах |
| `POSTGRES__DB`, `__HOST`, `__PORT`, `__USER`, `__PASSWORD` | — | Подключение к PostgreSQL (обязательные) |

## Kafka-топики

| Топик | Направление | Назначение |
|---|---|---|
| `ai_plot.novel.generate` | публикуем | Запрос на генерацию новеллы: `job_id`, `prompt`, `universe_id` |
| `ai_plot.scene.generate` | публикуем | Запрос на генерацию следующей сцены: `job_id`, `novel_id`, `scene_order`. Ключ сообщения — `novel_id`, чтобы сцены одной новеллы шли в одну партицию |
| `generation.results` | читаем | Результат генерации новеллы или сцены: `job_id`, `status` (`done` или `failed`), `result_id` (обязателен при `done`), `error` |

Для нового входящего топика нужно сделать две вещи: добавить топик в `init-topics.sh` и зарегистрировать обработчик в `TOPIC_HANDLERS` в [src/inbound/kafka/handlers/\_\_init\_\_.py](src/inbound/kafka/handlers/__init__.py).

Новые топики добавляются в массив `TOPICS` в [scripts/kafka/init-topics.sh](scripts/kafka/init-topics.sh).

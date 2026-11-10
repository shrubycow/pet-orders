# pet-orders

Приложение для обработки заказов. Сейчас оно в разработке: уже есть регистрация пользователя, подтверждение email, организация и каталог товаров.

Стек: Python 3.13, FastAPI, SQLAlchemy 2 (asyncpg), Alembic, PostgreSQL 18, RabbitMQ 4, Redis 8. Локальная почта — Mailpit. Зависимости ставятся через [uv](https://docs.astral.sh/uv/).

## Запуск

```bash
cp .env.example .env
docker compose up --build
docker compose exec api alembic upgrade head
```

`cp` копирует образец настроек в локальный `.env`. Этот файл в git не входит. `docker compose` поднимает Postgres, RabbitMQ, Redis, API и воркер. Файл `docker-compose.override.yml` добавляет Mailpit и reload API при изменении `src/`.

| Сервис | Адрес |
| --- | --- |
| API | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| RabbitMQ | http://localhost:15672 (`pet` / `pet`) |
| Mailpit | http://localhost:8025 |

Миграции при старте контейнера не применяются: после первого запуска и после новых ревизий нужна команда `alembic upgrade head` выше.

Без Docker API и воркер запускаются из корня репозитория и читают тот же `.env`. В образце хосты — имена сервисов Compose (`postgres`, `rabbitmq`, `redis`, `mailpit`). Для процесса на хосте замените их на `localhost`.

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn pet_orders.main:app --reload
uv run python -m pet_orders.worker
```

## Конфигурация

Переменные читаются из окружения и из `.env`. Образец — `.env.example`.

Обязательны `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY` (подпись JWT и хеш кода подтверждения) и `RABBITMQ_URL`. Без `RABBITMQ_URL` приложение не стартует: исключение одно — `ENVIRONMENT=test`. Сервисы `api` и `worker` берут все переменные из `.env`.

## Как устроен сценарий

1. `POST /users/` создаёт неактивного пользователя, отдаёт пару JWT и публикует событие в очередь `user_created`.
2. Воркер (`python -m pet_orders.worker`) кладёт хеш кода в Redis и отправляет код на email.
3. `POST /auth/verify-email` сверяет код и переводит пользователя в `active`.
4. Активный пользователь создаёт организацию (`POST /organizations/`) и становится её владельцем.
5. Участник активной организации создаёт товар (`POST /products/`). SKU уникален внутри организации.

Удаление записей запрещено в ORM. Не проходят ни `session.delete`, ни массовый `DELETE`.

## API

| Метод | Путь | Кто вызывает |
| --- | --- | --- |
| `GET` | `/health` | без авторизации |
| `POST` | `/users/` | без авторизации, лимит по IP |
| `POST` | `/auth/login` | без авторизации |
| `POST` | `/auth/refresh` | refresh-токен |
| `POST` | `/auth/verify-email` | неактивный пользователь |
| `POST` | `/auth/resend-auth-code` | неактивный пользователь |
| `POST` | `/organizations/` | активный пользователь |
| `POST` | `/products/` | участник организации |

Тела запросов, заголовок авторизации и примеры ошибок — в Swagger: http://localhost:8000/docs

## Тесты

Pytest читает `.env.test` из корня до импорта приложения. Там `ENVIRONMENT=test`, поэтому `RABBITMQ_URL` не нужен: при старте приложение к брокеру не подключается, а в тестах канал подменяется. `DATABASE_URL` указывает на `pet_orders_test`: фикстуры создают эту базу через `ADMIN_DATABASE_URL` и накатывают миграции до `head`. Redis — база `1` на опубликованном порту Compose, чтобы не задеть локальные сессии в `/0`. Postgres и Redis должны быть запущены.

```bash
uv sync --group dev
uv run pytest
```

## Миграции

Ревизии лежат в `src/pet_orders/migrations`. Имена ограничений и индексов задаёт `naming_convention` в `src/pet_orders/core/db/db.py`. Применить ревизии — `alembic upgrade head` из раздела «Запуск».

```bash
uv run alembic revision --autogenerate -m "short description"
```

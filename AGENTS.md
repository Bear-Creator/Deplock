# Project Architecture & State

## 1. Architecture Decision Records (ADR)
* **ADR-001**: Разделение Control Plane (FastAPI) и Data Plane (целевые серверы).
* **ADR-002**: Маршрутизация через Traefik на базе Docker labels для автоматического service discovery без перезагрузок proxy. Traefik контейнер маунтит `docker.sock` для считывания events.
* **ADR-003**: Связь FastAPI с удаленными Docker daemon через SSH-контекст (`docker-py`).
* **ADR-004**: Terraform используется для тестового стенда. Быстрый провижининг инфраструктуры через DigitalOcean API.
* **ADR-005**: Развёртывание целевых хостов (роли: `docker`, `traefik`) полностью автоматизировано через Ansible плейбуки с идемпотентностью.

## 2. Current State
### Stage 1: Core Architecture (Completed)
* [x] Определение высокоуровневой архитектуры.
* [x] Определение структуры проекта.
* [x] Инициализация базового скелета FastAPI.
* [x] Проектирование и реализация слоев FastAPI (Routers, Services, Schemas).
* [x] Интеграция Docker SDK for Python (SSH transport).
* [x] Написание Terraform манифестов для тестового стенда.
* [x] Написание Ansible плейбуков (Docker + Traefik).

### Stage 2: State Management & Database
* [x] Выбор и инициализация ORM (SQLAlchemy) + миграции (Alembic).
* [x] Проектирование и создание БД моделей `Server` и `Project`.
* [x] CRUD API для управления серверами.
* [x] Интеграция данных серверов в `RemoteDockerClient` (уход от хардкода).

### Stage 3: Lifecycle Management & Proxy Routing
* [x] Развёртывание проектов через POST API.
* [x] Список проектов и получение деталей через GET API.
* [x] Удаление проектов и остановка/удаление Docker контейнеров (DELETE API).
* [x] Интеграция с логами Docker.
* [x] Поддержка GitHub Webhooks (CD).

## 3. Known Bugs / Issues
* (Пусто)

## 4. Контекст для ИИ-Агентов (Onboarding)
**Deplock** — это легковесный аналог Coolify.
1. **Control Plane**: FastAPI сервис с асинхронным SQLite (SQLAlchemy 2.0 + Alembic). Служит для управления состоянием серверов (`Server`) и деплоев (`Project`).
2. **Data Plane**: Управление удалёнными серверами идёт через `docker-py` по SSH транспорт (`base_url="ssh://<user>@<ip>"`). Не используется агент на самом сервере(свой REST).
3. **Маршрутизация (Traefik)**: На Target-узлах поднят Traefik, читающий `docker.sock`. Контейнеры получают свои роуты через передачу Labels на этапе развёртывания.
4. **Тестирование (TDD)**:
   - Полное покрытие тестами `pytest`, `pytest-cov`, `httpx` (AsyncClient).
   - Инфраструктурные зависимости (Docker daemon по SSH) мокаются через Dependency Injection в FastAPI (переопределение в `conftest.py`).
   - Перед написанием кода писать тесты. В данный момент Coverage составляет ~92%.
5. **Требования к коду и стилю агента**:
   - Строгий TDD.
   - Осмысленные Git коммиты.
   - Никаких длинных приветствий и "словоблудия".
   - Использовать `ty-check` и `ruff format / ruff check`.
   - Любая новая логика или эндпоинты должны покрываться тестами так, чтобы покрытие не падало.

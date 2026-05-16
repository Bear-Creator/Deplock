# Project Architecture & State

## 1. Architecture Decision Records (ADR)

* **ADR-001**: Разделение Control Plane (FastAPI) и Data Plane (целевые серверы).
* **ADR-002**: Маршрутизация через Traefik на базе Docker labels для автоматического service discovery без перезагрузок proxy. Traefik контейнер маунтит `docker.sock` для считывания events.
* **ADR-003**: Связь FastAPI с удаленными Docker daemon через SSH-контекст (`docker-py`).
* **ADR-004**: Terraform используется для тестового стенда. Быстрый провижининг инфраструктуры через DigitalOcean API.
* **ADR-005**: Развёртывание целевых хостов (роли: `docker`, `traefik`) полностью автоматизировано через Ansible плейбуки с идемпотентностью.
* **ADR-006**: Для Frontend выбран стек: Vue 3 + Vite + Tailwind CSS + Vue Router + Axios.
* **ADR-007**: Desktop-оболочка реализована через `pywebview`. FastAPI локально поднимается из `main.py` и сам отдает собранный `frontend/dist`. Tauri удалён из активной архитектуры.

## 2. Current State

### Stage 1: Core Architecture (Completed)

* [x] Определение высокоуровневой архитектуры.
* [x] Определение структуры проекта.
* [x] Инициализация базового скелета FastAPI.
* [x] Проектирование и реализация слоев FastAPI (Routers, Services, Schemas).
* [x] Интеграция Docker SDK for Python (SSH transport).
* [x] Написание Terraform манифестов для тестового стенда.
* [x] Написание Ansible плейбуков (Docker + Traefik).

### Stage 2: State Management & Database (Completed)

* [x] Выбор и инициализация ORM (SQLAlchemy) + миграции (Alembic).
* [x] Проектирование и создание БД моделей `Server` и `Project`.
* [x] CRUD API для управления серверами.
* [x] Интеграция данных серверов в `RemoteDockerClient` (уход от хардкода).

### Stage 3: Lifecycle Management & Proxy Routing (Completed)

* [x] Развёртывание проектов через POST API.
* [x] Список проектов и получение деталей через GET API.
* [x] Удаление проектов и остановка/удаление Docker контейнеров (DELETE API).
* [x] Интеграция с логами Docker.
* [x] Поддержка GitHub Webhooks (CD).

### Stage 4: Web UI (Completed at Basic CRUD Level)

* [x] Инициализация Vue 3 + Vite + Tailwind CSS.
* [x] Реализация страниц управления серверами.
* [x] Реализация страниц управления деплоями.
* [x] Подключение API к бэкенду.

### Stage 5: Desktop Runtime (Completed)

* [x] Локальный launcher в `main.py`, который поднимает FastAPI и открывает `pywebview`.
* [x] Backend отдает `frontend/dist` без внешнего браузера.
* [x] Сборка desktop-приложения через `build.py` + PyInstaller.
* [x] Зафиксировано требование Python `3.13` для Windows desktop runtime.

## 3. Known Bugs / Issues

* Миграция `backend/alembic/versions/dd2a05c3fca2_add_use_https.py` некорректна и не должна использоваться как рабочая миграция в текущем виде.
* `deplock.db` является локальным dev-артефактом. Не считать его эталонным состоянием схемы или данных.
* Для старых локальных SQLite баз приложение делает dev-совместимую автопочинку недостающих колонок (`servers.is_active`, `projects.use_https`) на старте.

## 4. Контекст для ИИ-Агентов (Onboarding)

**Deplock** — это легковесный аналог Coolify.

1. **Control Plane**: FastAPI сервис с асинхронным SQLite (SQLAlchemy 2.0 + Alembic). Служит для управления состоянием серверов (`Server`) и деплоев (`Project`).
2. **Data Plane**: Управление удалёнными серверами идёт через `docker-py` по SSH транспорт (`base_url="ssh://<user>@<ip>"`). Не используется агент на самом сервере.
3. **Маршрутизация (Traefik)**: На target-узлах поднят Traefik, читающий `docker.sock`. Контейнеры получают свои роуты через labels на этапе развёртывания.
4. **Desktop Runtime**: `main.py` поднимает локальный FastAPI на `127.0.0.1`, ждёт `/health`, затем открывает `pywebview`. UI загружается из `frontend/dist`, который отдается самим backend.
5. **Python Version Constraint**: Для Windows desktop режима использовать Python `3.13`. Не возвращать проект на `3.14`, пока не решена совместимость `pywebview/pythonnet`.
6. **Frontend Workflow**: После изменений во frontend нужно пересобрать `frontend/dist`, иначе desktop launcher покажет старую сборку.
7. **Тестирование (TDD)**:
   - Полное покрытие тестами `pytest`, `httpx`.
   - Инфраструктурные зависимости мокаются через Dependency Injection в FastAPI.
   - Новая логика должна сопровождаться тестами.
8. **Требования к коду и стилю агента**:
   - Строгий TDD.
   - Использовать `ruff check`, `ruff format`, `ty check` когда окружение это позволяет.
   - Любая новая логика или эндпоинты должны покрываться тестами так, чтобы покрытие не падало.
   - Не тащить обратно Tauri-файлы и Tauri-зависимости без отдельного решения пользователя.

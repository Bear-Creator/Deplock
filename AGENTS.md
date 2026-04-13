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

## 3. Known Bugs / Issues
* (Пусто)

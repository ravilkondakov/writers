# Литстенд: каркас платформы для авторов

Учебный стенд и основа будущей платформы. Стек: Django + DRF, PostgreSQL, Redis,
Celery + RabbitMQ, Kafka, Docker Compose, pytest, GitLab CI.

> **Статус проверки.** Файлы собраны без запуска: в среде, где писался каркас, не было доступа
> к PyPI и Docker. Прошли только проверки синтаксиса Python и YAML. Первый запуск у вас на машине
> и есть настоящая проверка. Ошибки при старте это нормально: пришлите текст ошибки целиком.

## Запуск (3 команды)

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f web      # дождитесь строки "Starting development server"
```

- API: http://localhost:8000/api/stories/
- Админка: `docker compose exec web python manage.py createsuperuser`, затем http://localhost:8000/admin/
- RabbitMQ: http://localhost:15672 (guest / guest)
- После первого старта закоммитьте появившиеся `apps/*/migrations/0001_initial.py`.

Без Docker (быстрый режим, SQLite, без очередей): `pip install -r requirements-dev.txt && pytest -q`.

## Быстрая проверка руками

```bash
# регистрация, в ответе токен
curl -X POST localhost:8000/api/auth/register/ -d "username=ivan&password=secret123&pen_name=Иван"
# создать жанр (через админку), затем рассказ
curl -X POST localhost:8000/api/stories/ -H "Authorization: Token <токен>" \
     -d "title=Тест&text=Текст&genre=1"
curl -X POST localhost:8000/api/stories/1/publish/ -H "Authorization: Token <токен>"
```

После публикации в логах `worker` появится «Notify subscribers», а при просмотре
рассказа `GET /api/stories/1/` consumer увеличит `views_count`.

## Структура

```
config/            настройки, Celery, urls
apps/authors/      профиль автора, регистрация, токены
apps/stories/      рассказы: модели, API, selectors (запросы), tasks (Celery)
apps/reviews/      отзывы и оценки; seed_data для больших данных
apps/events/       Kafka: producer (в API) и consumer (отдельный процесс)
tests/             pytest
docs/              ARCHITECTURE.md, outreach.md
```

## Учебный план: что дописываете вы

В коде есть пометки `TODO(вечер 1)` и `TODO(вечер 2)`. Логику пишете сами: так знания закрепляются.

**Вечер 1: PostgreSQL, DRF, Redis, тесты**
- [ ] Запустить стенд и пройти «Быструю проверку»
- [ ] `make seed`, замерить `/api/stories/top/?genre=genre-0&days=7`
- [ ] Починить N+1 в списке рассказов (`serializers.py`, `views.py`), снять `xfail` в `tests/test_query_counts.py`
- [ ] Переписать `selectors.top_stories` в один запрос, показать `EXPLAIN ANALYZE` до и после индекса
- [ ] Закэшировать top в Redis (cache-aside, TTL)
- [ ] Написать 3 своих теста

**Вечер 2: очереди и события**
- [ ] Celery: идемпотентность `notify_story_published`, отдельная очередь, найти её в RabbitMQ
- [ ] Kafka: consumer читает пачками, защита от дублей по `event_id`, запустить 2 consumer с одной группой и увидеть разделение партиций
- [ ] Объяснить вслух своими словами: чем RabbitMQ отличается от Kafka и почему тут нужны оба
- [ ] Прогнать `ruff check .` и `pytest`

## Чего здесь сознательно нет

Фронтенда, ридера, донатов, рассылок, поиска. Это не нужно, пока нет авторов. Из «плюсов» вакансии
не сделаны Prometheus, Elasticsearch и Ansible: можно честно называть их пробелом.

.PHONY: up down logs migrations migrate test seed shell lint

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f web worker consumer

migrations:
	docker compose exec web python manage.py makemigrations

migrate:
	docker compose exec web python manage.py migrate

test:
	docker compose exec web pytest -q

seed:
	docker compose exec web python manage.py seed_data --stories 5000 --reviews 1000000

shell:
	docker compose exec web python manage.py shell

lint:
	docker compose exec web ruff check .

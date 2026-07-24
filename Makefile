.PHONY: install run-api run-frontend run-celery run-pipeline clean health

install:
	pip install -e .[dev]

run-api:
	python -m api.api_server

run-frontend:
	cd frontend && npm run dev

run-celery:
	python -m celery -A api.celery_worker.celery_app worker --loglevel=info --pool=solo

run-pipeline:
	python -m pipeline.processing.run_pipeline

health:
	python api/health_check.py

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

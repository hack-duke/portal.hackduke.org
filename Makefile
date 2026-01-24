SHELL := /bin/bash
.PHONY: rebuild up shell backend test

rebuild: # If you have issues try running devcontainer up --workspace-folder . --remove-existing-container --build-no-cache
	@devcontainer up --workspace-folder . --remove-existing-container 

up:
	@devcontainer up --workspace-folder .

shell:
	@devcontainer exec --workspace-folder . zsh

backend:
	cd portal-backend-python && source ./load_env.sh && export PYTHONPATH=/workspaces/portal.hackduke.org && poetry install && poetry run uvicorn server:app --reload

backend-test-db:
	cd portal-backend-python && source ./load_env.sh && export DB_NAME=test && export PYTHONPATH=/workspaces/portal.hackduke.org && poetry install && poetry run uvicorn server:app --reload

frontend:
	cd portal-frontend && source ./load_env.sh && npm install && npm start

test:
	cd portal-backend-python && source ./load_env.sh && export PYTHONPATH=/workspaces/portal.hackduke.org && poetry install && poetry run pytest

env:
	cd portal-backend-python && source ./load_env.sh
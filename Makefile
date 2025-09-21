.PHONY: rebuild up shell backend test

rebuild: # If you have issues try running devcontainer up --workspace-folder . --remove-existing-container --build-no-cache
	@devcontainer up --workspace-folder . --remove-existing-container 

up:
	@devcontainer up --workspace-folder .

shell:
	@devcontainer exec --workspace-folder . zsh

backend:
	cd portal-backend-python && PYTHONPATH=/workspaces/portal.hackduke.org uvicorn server:app --reload

frontend:
	cd portal-frontend && npm start

test:
	pytest
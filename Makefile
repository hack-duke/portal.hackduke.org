.PHONY: rebuild up shell

rebuild: # If you have issues try running devcontainer up --workspace-folder . --remove-existing-container --build-no-cache
	@devcontainer up --workspace-folder . --remove-existing-container 

up:
	@devcontainer up --workspace-folder .

shell:
	@devcontainer exec --workspace-folder . zsh

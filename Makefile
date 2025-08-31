.PHONY: rebuild up shell

rebuild: # Triggers extension updates
	@devcontainer up --workspace-folder . --remove-existing-container 

up:
	@devcontainer up --workspace-folder .

shell:
	@devcontainer exec --workspace-folder . zsh

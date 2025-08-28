.PHONY: up shell

up:
	@devcontainer up --workspace-folder .

shell:
	@devcontainer exec --workspace-folder . zsh

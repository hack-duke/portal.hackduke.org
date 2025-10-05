# Development Environment
This project uses a Dev Container for a consistent development environment across machines. The container is defined in `.devcontainer/devcontainer.json` and built from a custom Dockerfile.

## Requirements
- Docker
- VS Code or Cursor with the Dev Containers extension

## Option 1: Starting Container from VSCode
Ensure you have the Dev Containers extension installed. If not, open the Extensions tab (Command + Shift + X) and search for `Dev Containers`. Install.

Open the project root directory.

A popup should appear notifying you that a devcontainer environment is available. Click `Reopen in Container`.

If not, you can do this manually by opening the command palette (Command + Shift + P)  and searching for `Dev Containers: Reopen in Container`  

## Option 2: Starting Container from Terminal

> ❗ This is currently experimental and sometimes fails to link the `devcontainer.json` config to the running container. If anything is not working, switch to starting directly form VSCode/Cursor.

Make sure you have the Dev Containers CLI installed. If not, you can install with:
```
npm install -g @devcontainers/cli
```

To build and start the devcontainer:
```
make up
```

To open a shell inside the container:
```
make shell
```

To attach your VSCode/Cursor instance to the running container:
1. Open the command palette and search for `Dev Containers: Attach to Running Container`
2. Connect to your running container
3. Open Folder and navigate to the project root (located at `../workspaces/portal.hackduke.org`) 

## Setting up Git
> Sharing Git credentials from the host machine to the container is [possible](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials), but is probably more trouble than it is worth.

Open a terminal in the devcontainer and generate a SSH key.
```
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Copy the public key
```
cat ~/.ssh/id_ed25519.pub
```

Navigate to [GitHub settings](https://github.com/settings/keys):
- Click New SSH key or Add SSH key.
- Paste the copied public key into the Key field.
- Click Add SSH key. You may be prompted to confirm your GitHub password.

Set up your name or email address if prompted.
```
git config --global user.name "Your Name"
git config --global user.email "your.email@address"
```

## Optional Configuration

Devcontainers comes pre-installed with [Oh My Zsh](https://github.com/ohmyzsh/ohmyzsh). 

Consider installing [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions/tree/master) for autocomplete.


```
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
```

Add the zsh-autosuggestions plugin to `~/.zshrc`
```
plugins=( 
    # other plugins...
    zsh-autosuggestions
)
```

Add the following line to your `~/.zshrc` before configuring plugins. This ensures truecolor is properly supported so that ghost text displays properly.
```
export TERM=xterm-256color
```

Accept suggestions with → or Ctrl + E.

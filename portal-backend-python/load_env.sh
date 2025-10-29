#!/usr/bin/env bash
# Script to authenticate with Vault and load environment variables for backend

VAULT_ADDR="http://db:8200"
TOKEN_FILE="./.vault_token"
KV_PATH="secrets/backend"

export VAULT_ADDR

_try_token_login() {
  local token="$1"
  if vault login "$token" >/dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

if [[ -f "$TOKEN_FILE" ]]; then
  saved_token="$(<"$TOKEN_FILE")"
  echo "Found existing token at $TOKEN_FILE — attempting login..."
  if _try_token_login "$saved_token"; then
    echo "Login with saved token succeeded."
  else
    echo "Saved token failed."
    saved_token=""
  fi
fi

if [[ -z "${saved_token:-}" ]]; then
  echo -n "Enter GitHub access token for Vault login (input hidden): "
  read -rs GITHUB_TOKEN
  echo
  if vault login -method=github token="$GITHUB_TOKEN" >/dev/null 2>&1; then
    echo "GitHub login succeeded."
    if vault token lookup >/dev/null 2>&1; then
      new_token="$(vault token lookup | awk '/^id[[:space:]]+/ {print $2}')"
    else
      if command -v jq >/dev/null 2>&1; then
        new_token="$(vault token lookup -format=json | jq -r '.data.id')"
      else
        echo "couldn't parse token from 'vault token lookup' output. "
        exit 1
      fi
    fi

    if [[ -n "${new_token:-}" ]]; then
      printf "%s" "$new_token" > "$TOKEN_FILE"
      chmod 600 "$TOKEN_FILE"
      echo "Stored new token to $TOKEN_FILE."
    else
      echo "Error: login succeeded but failed to extract token."
      exit 1
    fi
  else
    echo "GitHub login failed. Exiting."
    exit 1
  fi
fi

echo "Fetching secrets from Vault ($KV_PATH) and exporting into environment..."

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  key="${line%%=*}"
  value="${line#*=}"
  export "$key=$value"
  printf "exported %s\n" "$key"
done < <(vault kv get -format=json "$KV_PATH" | jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"')


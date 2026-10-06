#!/usr/bin/env bash
# Script to authenticate using AWS IAM role and populate .env -- PROD USE ONLY

set -euo pipefail
umask 077

export VAULT_ADDR="http://db:8200"

vault login -method=aws role=backend-ec2

env_tmp="$(mktemp .env.XXXXXX)"
cleanup() {
  rm -f -- "$env_tmp"
}
trap cleanup EXIT

vault kv get -format=json secrets/backend_prod \
  | jq -er '.data.data | to_entries[] | "\(.key)=\(.value)"' > "$env_tmp"

chmod 600 "$env_tmp"
mv -f -- "$env_tmp" .env
trap - EXIT

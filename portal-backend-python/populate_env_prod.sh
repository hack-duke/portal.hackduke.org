#!/usr/bin/env bash
# Script to authenticate using AWS IAM role and populate .env -- PROD USE ONLY

set -euo pipefail
umask 077

export VAULT_ADDR="http://db:8200"

required_keys=(
  DB_HOST
  DB_USER
  DB_PASSWORD
  DB_NAME
  AUTH0_DOMAIN
  AUTH0_API_AUDIENCE
  AUTH0_ISSUER
  AUTH0_ALGORITHMS
  AUTH0_MGMT_CLIENT_ID
  AUTH0_MGMT_CLIENT_SECRET
  AUTH0_DB_CONNECTION
  FRONTEND_URL
  SES_FROM_EMAIL
  SES_REGION
  PORTAL_PUBLIC_URL
)

validate_env_file() {
  local env_file="$1"
  local key

  if [[ ! -s "$env_file" ]]; then
    echo "Production environment file is missing or empty" >&2
    return 1
  fi

  for key in "${required_keys[@]}"; do
    if ! grep -Eq "^${key}=.+$" "$env_file"; then
      echo "Production environment is missing a nonempty ${key}" >&2
      return 1
    fi
  done
}

if [[ "${1:-}" == "--validate-existing" ]]; then
  validate_env_file "${2:-.env}"
  chmod 600 "${2:-.env}"
  exit 0
elif [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--validate-existing [path]]" >&2
  exit 2
fi

# Capture the token without printing or persisting it. GitHub Actions receives
# the SSH output, so the default human-readable login response is unsafe here.
export VAULT_TOKEN
VAULT_TOKEN="$(vault login \
  -method=aws \
  -no-store \
  -token-only \
  role=backend-ec2)"

env_tmp="$(mktemp .env.XXXXXX)"
cleanup() {
  rm -f -- "$env_tmp"
}
trap cleanup EXIT

vault kv get -format=json secrets/backend_prod \
  | jq -er '
      .data.data as $values
      | if ($values | type) != "object" then
          error("Vault secret must be an object")
        elif any(
          $values | to_entries[];
          ((.key | test("^[A-Za-z_][A-Za-z0-9_]*$") | not)
            or ((.value | type) != "string")
            or (.value | contains("\n") or contains("\r") or contains("\u0000")))
        ) then
          error("Vault secret contains an invalid environment entry")
        else
          $values | to_entries[] | "\(.key)=\(.value)"
        end
    ' > "$env_tmp"

validate_env_file "$env_tmp"
chmod 600 "$env_tmp"
mv -f -- "$env_tmp" .env
trap - EXIT

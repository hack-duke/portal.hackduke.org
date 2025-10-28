#!/usr/bin/env bash

export VAULT_ADDR="http://db:8200"

vault login -method=aws role=backend-ec2

vault kv get -format=json secrets/backend_prod | jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"' > .env
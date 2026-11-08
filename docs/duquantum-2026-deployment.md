# DuQuantum 2026 deployment runbook

This is a manual, two-person production checklist. It does not authorize a
deployment by itself. Record the release Git SHA, immutable ECR image tag,
database backup path, Alembic revisions, Netlify deploy ID, and operators in the
private change record.

## 1. Preflight and staging

1. Confirm the worktree does not contain the private CSV, environment files,
   database dumps, account setup tokens, or email exports. `git check-ignore` must
   identify `data/private/`.
2. Run backend tests and a clean frontend production build.
3. Build the backend image from the exact release SHA and tag it with that SHA;
   do not rely on `latest` for rollback.
4. Restore a recent sanitized production dump into an isolated staging
   database. Test `alembic current`, `alembic heads`, and `alembic upgrade head`
   there. A fresh empty database must also upgrade from base to head.
5. Run the private CSV importer offline, then `--database-check` against staging.
   Commit it only in staging and reconcile the expected aggregate totals.
6. Exercise attendee login/claim, admin list/detail, pass rendering, valid and
   invalid scans, event isolation, and an SES synthetic test recipient.
7. Obtain a go/no-go approval before touching production.

Do not run Alembic while it prints a full database URL. A database URL contains
credentials and must never enter CI, shell history, or deployment logs.

## 2. Configuration inventory

Verify secret names and values exist in the production secret manager without
printing values:

- Database: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- Backend/Auth0: `AUTH0_DOMAIN`, `AUTH0_API_AUDIENCE`, Management API client
  credentials, database connection, and `ACCOUNT_SETUP_TTL_SECONDS`. The M2M
  client needs exactly `read:users`, `create:users`, and `update:users`.
- Frontend: `REACT_APP_AUTH0_DOMAIN`, `REACT_APP_AUTH0_CLIENT_ID`,
  `REACT_APP_AUTH0_AUDIENCE`, and `REACT_APP_BACKEND_URL`.
- Web: `FRONTEND_URL` must exactly match the production portal origin used by
  backend CORS. Include staging separately; never use a wildcard with
  credentials.
- Email: `SES_FROM_EMAIL`, `SES_REGION`, `PORTAL_PUBLIC_URL`, and optional SES
  configuration set.
- Web Push: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`, and
  `EVENT_NOTIFICATIONS_ENABLED`. Keep the private key in Vault and preserve the
  same VAPID identity across deployments so existing device subscriptions stay
  valid.

In Auth0, explicitly list the exact production and staging URLs under Allowed
Callback URLs, Allowed Logout URLs, and Allowed Web Origins. Include the real
Auth0 callback path used by the SPA and both canonical URL/trailing-slash forms
only when the application actually emits both. Do not use wildcard domains.

Verify the SES sender/domain in the selected region, DKIM, SPF, DMARC,
production-sandbox exit, quota, and bounce/complaint destinations. Run only the
synthetic test before production data is imported.

## 3. Database backup and migration

Put the application into a brief maintenance window if schema migration and
old application writes can race. On the database host, create a custom-format
backup using credentials supplied from its protected environment—not embedded
in the command or shell history:

```sh
umask 077
mkdir -p "$BACKUP_DIR"
docker exec postgres_db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --format=custom --no-owner --no-acl > "$BACKUP_DIR/portal-pre-duquantum.dump"
test -s "$BACKUP_DIR/portal-pre-duquantum.dump"
```

Store the backup in encrypted, access-controlled storage and perform a test
restore in staging. Capture the current revision, then migrate using the same
immutable backend image that will serve traffic:

```sh
docker run --rm --env-file .env RELEASE_IMAGE alembic current
docker run --rm --env-file .env RELEASE_IMAGE alembic heads
docker run --rm --env-file .env RELEASE_IMAGE alembic upgrade head
docker run --rm --env-file .env RELEASE_IMAGE alembic current
```

There must be exactly one Alembic head. Stop if migration output contains a
secret, if a revision differs from staging, or if any step fails.

## 4. Backend ECR and EC2

The existing GitHub workflow builds ARM64, pushes to ECR, copies Compose/Caddy
configuration to EC2, and restarts Compose. Before release, change the deployed
Compose image from mutable `latest` to the recorded immutable image tag or
digest. Keep the previous tag available.

After migrations succeed:

1. Pull the recorded release image on EC2.
2. Populate `.env` from the secret manager with mode `0600`.
3. Run `docker-compose config` and confirm it does not print or persist secrets
   into the change record.
4. Start the backend and reverse proxy, then inspect container health and only
   PII-safe logs.
5. Request `/health`, verify TLS, and test CORS once from the staging or
   production portal origin.

The backend workflow runs `alembic upgrade head` from the freshly pulled,
immutable release image before setting `BACKEND_IMAGE` and invoking Compose.
The remote shell uses fail-fast behavior, so a migration failure leaves the old
backend container running and prevents rollout of the new image.

## 5. Private production import

Transfer the CSV directly to a mode-`0600` file on the backend host over an
encrypted channel. Do not upload it to GitHub Actions artifacts, Netlify, ECR,
or the Docker build context. Mount or copy it into a one-off backend container,
then run:

```sh
python -m scripts.import_event_registrations --input /run/private/confirmation_responses.csv
python -m scripts.import_event_registrations --input /run/private/confirmation_responses.csv --database-check
python -m scripts.import_event_registrations --input /run/private/confirmation_responses.csv --commit --confirm-event duquantum-2026
python -m scripts.import_event_registrations --input /run/private/confirmation_responses.csv --database-check
```

Reconcile totals in the admin UI. Securely remove the host CSV after successful
reconciliation and backup; retain the organizer's protected source of record.

## 6. Frontend and Netlify

Build with production environment variables, inspect the deploy preview, and
confirm no secret or source map contains attendee data. Deploy the exact tested
commit to Netlify. Verify direct navigation/refresh on participant, admin, and
scanner routes; Auth0 redirect/login/logout; mobile QR layout; and backend CORS.
Only public Auth0 SPA values belong in frontend environment variables.

## 7. Production smoke test

Use dedicated test identities and synthetic records, then remove or clearly
label them:

- Backend `/health` and authenticated current-event endpoint.
- Accepted verified user claim, unaccepted user denial, and email mismatch path.
- Admin event list and all imported structured fields.
- Active pass, malformed pass, wrong-event pass, revocation, first scan, and
  duplicate scan per checkpoint.
- Synthetic SES test, database delivery audit, and already-sent skip.
- Home Screen install on Android and iOS, explicit notification opt-in, local
  confirmation notification, one synthetic Web Push delivery, unsubscribe,
  and stale-subscription deactivation. Do not advance the production schedule
  or send a real event alert during a smoke test.
- Single-use portal account setup, expired/reused token rejection, Auth0 login,
  and verified-email registration claim.
- No attendee values, database URLs, setup tokens, passwords, or JWTs in
  logs/Sentry.

Only after smoke tests pass should operators send the attendee campaign.

## 8. Rollback

For an application-only defect, stop sends/imports, route EC2 Compose back to
the previous immutable image, redeploy the previous Netlify release, and repeat
health/login checks. Forward-fix additive event tables when possible.

For a migration defect, first stop all backend writers and preserve a new dump
for investigation. Use `alembic downgrade <previous_revision>` only if the
tested downgrade is non-destructive and no new production data would be lost.
Otherwise restore the verified pre-release dump into a new database instance,
point the previous backend release at it, and validate counts before reopening
traffic. Never overwrite the only production database or backup in place.

If an email batch has begun, it cannot be recalled. Stop subsequent sends,
retain delivery audit rows, and communicate corrections through an approved
operational campaign. Revoke compromised passes or setup links individually;
do not delete attendee records as a first response.

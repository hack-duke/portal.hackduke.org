# DuQuantum 2026 portal operations

This runbook covers the private attendance-confirmation import, Auth0 account
access, and attendee email. Commands are run from `portal-backend-python` unless
stated otherwise.

## Private data handling

The local source file is kept at
`data/private/duquantum-2026/confirmation_responses.csv`. The entire
`data/private/` tree is Git-ignored. Verify this before every commit:

```powershell
git check-ignore -q -- data/private/duquantum-2026/confirmation_responses.csv
if ($LASTEXITCODE -ne 0) { throw "Private CSV is not ignored" }
git status --short --ignored data/private
```

Never paste CSV rows, attendee emails, phone numbers, Auth0 tickets, database
exceptions, or email provider request bodies into logs or issue trackers. Do
not use this file as a test fixture. Delete the production-host copy after the
import totals have been reconciled and an encrypted database backup exists.

The confirmation file is interpreted as accepted and RSVP-confirmed. Exact
answers are retained in `source_data`, while common admin fields and five
consent choices are stored in structured columns. The MLH/DEV occasional-email
choice is `mlh_marketing_opt_in`; an opt-out must be honored for nonessential
marketing. Account access, pass delivery, safety, and schedule updates are
operational messages and are not marketing.

## Import registrations

The importer is offline and dry-run by default. It normalizes emails using trim
and case-fold only, validates fields, and keeps the newest timestamp within each
duplicate-email group.

```powershell
python -m scripts.import_event_registrations
```

Expected source reconciliation for the supplied file:

- 53 response rows
- 48 unique valid registrations
- 5 duplicate-email groups and 5 older rows superseded
- 0 invalid rows

After database migrations and the `duquantum-2026` event seed exist, compare
without writing:

```powershell
python -m scripts.import_event_registrations --database-check
```

Commit only after both summaries are reviewed:

```powershell
python -m scripts.import_event_registrations `
  --commit `
  --confirm-event duquantum-2026
```

Rerun the database check. A rerun is idempotent: the unique event/email key is
updated instead of duplicated, and a database row from a newer source response
is not overwritten.

## Auth0 account policy

The normal and recommended flow is verified-email claim: an attendee signs in
or signs up in Auth0, verifies their email, and the backend atomically claims
the matching unclaimed event registration. No pre-created account is required.

Do **not** create passwords from last name, phone number, date of birth, or any
other attendee data. Those values are known to organizers and are frequently
guessable or reused. The onboarding tool cannot create such passwords.

If organizers decide that pre-provisioning is necessary, configure a dedicated
Auth0 database connection and a Management API machine-to-machine client with
only `read:users`, `create:users`, and `create:user_tickets`. Configure:

```text
AUTH0_DOMAIN
AUTH0_MGMT_CLIENT_ID
AUTH0_MGMT_CLIENT_SECRET
AUTH0_DB_CONNECTION
AUTH0_INVITATION_RETURN_URL=https://portal.hackduke.org/events/duquantum-2026
AUTH0_INVITATION_TTL_SECONDS=604800
```

Inventory first. This reads Auth0 but creates nothing:

```powershell
python -m scripts.onboard_event_auth0
```

Use a small controlled batch first. Provisioning creates a cryptographically
random temporary password that is never printed or stored, creates a
single-use password-change ticket that verifies mailbox ownership, and sends
that ticket through the configured SES sender. All four safety flags are
required:

```powershell
python -m scripts.onboard_event_auth0 `
  --create-missing --commit --send-invitations `
  --confirm-event duquantum-2026 --limit 2
```

Reconcile the aggregate result before removing the limit. An account that this
tool created but failed to invite remains tagged in Auth0 and can be safely
re-invited on a later explicit run. Existing unrelated accounts are never
assigned a new password or sent a reset link by this tool.

## SES operational campaigns

Configure `SES_FROM_EMAIL` to a verified DuQuantum sender identity,
`SES_REGION`, `PORTAL_PUBLIC_URL=https://portal.hackduke.org`, and optionally
`SES_CONFIGURATION_SET`. SPF, DKIM, DMARC, production access, bounce/complaint
handling, and sending quota must be verified in AWS before launch.

Preview aggregate counts without sending:

```powershell
python -m scripts.send_event_email_campaign --campaign pass-ready
```

Send a synthetic test containing no attendee data:

```powershell
python -m scripts.send_event_email_campaign `
  --campaign pass-ready --test-email organizer@example.org `
  --send --confirm-event duquantum-2026
```

For production, record the dry-run pending count exactly:

```powershell
python -m scripts.send_event_email_campaign `
  --campaign pass-ready --send `
  --confirm-event duquantum-2026 --confirm-recipient-count 48
```

The command requires the database delivery-audit table, queues an audit row
before each send, records the SES message ID, and skips already-sent campaign
recipients. Never bypass count confirmation. Start with a controlled cohort,
then send the remainder only after inspecting rendering and delivery events.

## Day-of-event reconciliation

- Export or print an encrypted/offline manual attendee roster as a fallback.
- Confirm every active QR resolves to the same event and registration shown in
  the admin view.
- Test a first scan, duplicate scan, wrong-event pass, revoked pass, manual
  lookup, and each configured checkpoint.
- Keep one staff account without broad admin permissions as the scanner test
  account.
- Monitor backend health, SES bounces/complaints, and check-in failures without
  including PII in logs.

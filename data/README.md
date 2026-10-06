# Private event data

`data/private/` is reserved for local attendee imports and generated operational
artifacts. The directory is ignored by Git. Its contents contain personal data
and must not be copied into issues, pull requests, logs, screenshots, or test
fixtures.

For DuQuantum 2026, the canonical local import path is:

`data/private/duquantum-2026/confirmation_responses.csv`

Only an operator who is authorized to manage attendee data should have access
to this directory. Production imports should be transferred directly to the
backend host over an encrypted channel, imported with the CLI in dry-run mode
first, and removed from the host after the database import and reconciliation
are complete. Database backups and email delivery exports containing attendee
data must use the same access controls and retention policy.

Do not use the confirmation CSV to send marketing messages to respondents who
did not opt in. Operational event messages (account access, pass readiness, and
schedule or safety changes) must use a separately named operational campaign.

# HackDuke portal restoration

The HackDuke design and application flow come from `ad3a0e7` (March 21, 2026),
the last default-branch commit before DuQuantum. Existing HackDuke application
dates and form definitions are retained; this restoration does not create a
new application season.

The complete DuQuantum implementation and commit history are preserved on the
remote branch `duquantum-2026`, pointing to
`58b243d4d6c90f22066fbadc1c14d51be5792d99`.

To inspect or run that version locally:

```sh
git fetch origin
git switch duquantum-2026
git pull --ff-only origin duquantum-2026
```

The default branch serves the HackDuke login, participant application, status,
legacy QR pass, and administrator pages. DuQuantum pages, operational workflows,
account setup, email campaigns, event endpoints, and notification delivery are
archived on the event branch. The old service-worker URL serves a retirement
worker so existing installations can unregister without loading event alerts.

Production migrations and event models remain on the default branch for
compatibility with the database already deployed. They are dormant schema
definitions, not enabled event APIs. No downgrade, table drop, attendee update,
Auth0 account change, invitation, or notification is part of this restoration.
Private local imports and exported spreadsheets remain ignored by Git and
are not stored on either branch.

Infrastructure fixes retained include disk cleanup, bounded Docker logs,
immutable release images, container/public health checks, migration-before-
replacement ordering, failed-release rollback, safe Vault token handling,
validated environment fallback, CI Python compatibility, and protected error
messages. Production retains its existing Vault secrets. HackDuke releases no
longer require event email/push settings or create/enable event push keys.

Returning the event to production later requires a reviewed restoration commit
on the default branch; merely merging its ancestor branch will not undo this
restoration. Revert the HackDuke restoration commit on a new branch and reconcile
subsequent infrastructure changes before testing and deploying. Event data can
then be used by the restored event code without rerunning imports or invitations.

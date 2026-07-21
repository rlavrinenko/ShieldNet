# ShieldNet v5.2.1

- Fixed `0037_verification_center` on databases where `verification.requests.updated_at` or other v5.2 objects already exist.
- Added idempotent checks for columns, the decisions table, and indexes.
- Re-running `alembic upgrade head` is now safe after the previous DuplicateColumn failure.

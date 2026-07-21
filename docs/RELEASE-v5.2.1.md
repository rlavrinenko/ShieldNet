# ShieldNet v5.2.1 Migration Fix

This hotfix replaces migration `0037_verification_center` with an idempotent version. It does not stamp or skip the migration: Alembic still applies and records revision `0037_verification_center` normally.

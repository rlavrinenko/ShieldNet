# ShieldNet v1.7.1 Hotfix

## Fixed

- Fixed backend startup on Python 3.12 when `MemberService.list()` shadowed the built-in `list` type used by a later return annotation.
- Added postponed annotation evaluation in `app/services/member_service.py`.
- Kept the shortened Alembic revision ID `0019_watchlist` compatible with `alembic_version.version_num VARCHAR(32)`.

## Validation

- `app.main` imported successfully in a clean virtual environment.
- Python `compileall` completed successfully for `app` and `alembic`.
- Alembic graph has one head: `0019_watchlist`.

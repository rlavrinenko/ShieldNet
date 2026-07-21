# ShieldNet v1.7 migration hotfix

The Alembic revision ID was shortened from `0019_member_watchlist_risk_review`
to `0019_watchlist` so it fits into PostgreSQL `alembic_version.version_num VARCHAR(32)`.

Run:

```bash
cd /opt/shieldnet/backend
source venv/bin/activate
alembic upgrade head
alembic current
```

Expected current revision: `0019_watchlist (head)`.

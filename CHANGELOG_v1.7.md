# ShieldNet 1.7.0

## Member Watchlist & Risk Review

- Added watchlist state to member profiles.
- Added low, medium, high and critical risk levels.
- Added review reason and scheduled review datetime.
- Added watchlist and overdue-review member filters.
- Added watchlist, high-risk and overdue-review statistics.
- Added risk badges in Members Control Center.
- Added Alembic revision `0019_member_watchlist_risk_review`.

## Validation

- Python source and Alembic revisions pass `python -m compileall`.
- Run `npm ci && npm run build` on the deployment server to validate and produce the Angular bundle.

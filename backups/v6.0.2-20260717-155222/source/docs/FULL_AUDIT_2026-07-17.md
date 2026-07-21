# ShieldNet full audit — 2026-07-17

## Confirmed runtime state

- Backend, Discord bot and scheduler were active in the supplied snapshot.
- Recent internal API requests returned HTTP 200.
- Python source for backend, bot, scheduler and Alembic migrations compiles successfully.
- Angular production build succeeds.

## Confirmed defects

### 1. Missing Leadership route

`LeadershipComponent`, its service, sidebar link and server quick-action existed, but `app.routes.ts` had no route for `/guild/:guildId/leadership`. Angular therefore redirected the request through the wildcard route to the dashboard.

**Correction:** register the missing guarded route.

### 2. Incorrect frontend publication assumption

Angular 20 writes the browser bundle to:

`dist/shieldnet-admin/browser/`

The failed installer validated/copied the parent output directory instead of the `browser` directory. Nginx serves `/var/www/shieldnet`, so `browser/index.html` must be copied into that web root.

**Correction:** the new installer detects the Angular browser output and publishes its contents directly to `/var/www/shieldnet`.

### 3. Incomplete PostgreSQL runtime grants

The database separates migration ownership (`shieldnet_owner`) from application access (`shieldnet_backend`). The supplied project had no migration that grants the runtime role access to newly created schemas/tables. This caused `permission denied for schema leadership` after the Leadership migration.

**Correction:** migration `0042_runtime_database_grants` grants current and default privileges across all ShieldNet schemas.

### 4. Incorrect Alembic diagnostic query

The archive script queried `public.alembic_version`, while this project configures `version_table_schema="system"`.

Correct query:

```sql
SELECT version_num FROM system.alembic_version;
```

### 5. Dependency audit warning

`npm ci` reports five moderate-severity dependency findings. They do not block the current production build. Automatic forced upgrades were not applied because they can introduce Angular breaking changes. Review with `npm audit` after the UI correction is deployed.

## Validation performed on the supplied source

- `npm ci --ignore-scripts`: completed.
- `npm run build`: completed successfully.
- `python3 -m compileall` for backend, bot, scheduler and migrations: completed successfully.
- Existing service snapshot: all three ShieldNet services active.

## Not claimed

The patch has been built and statically validated against the uploaded project. It has not been executed against the live production server or live production database from this environment.

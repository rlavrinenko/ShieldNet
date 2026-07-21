# ShieldNet v2.1.0

- Added central Guild Registry service.
- Fixed `verification.settings` foreign-key failures for unregistered guilds.
- OAuth registers owned guilds and active owner access.
- Bot registration now uses the central registry.
- Added superadmin-safe guild initialization.
- Added guild registry diagnostic API.
- Added migration `0023_registry`.

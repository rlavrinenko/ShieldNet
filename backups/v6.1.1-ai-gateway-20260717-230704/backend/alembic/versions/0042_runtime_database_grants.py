"""Ensure the runtime database role can use all ShieldNet schemas.

Revision ID: 0042_runtime_database_grants
Revises: 0041_setup_wizard
"""
from alembic import op

revision = "0042_runtime_database_grants"
down_revision = "0041_setup_wizard"
branch_labels = None
depends_on = None

SCHEMAS = (
    "audit", "campaigns", "core", "crm", "discord", "leadership",
    "messages", "moderation", "modules", "permissions", "security",
    "system", "verification",
)


def upgrade() -> None:
    schemas = ", ".join("'%s'" % s for s in SCHEMAS)
    op.execute(f"""
    DO $$
    DECLARE schema_name text;
    BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'shieldnet_backend') THEN
        GRANT CONNECT ON DATABASE shieldnet TO shieldnet_backend;
        FOREACH schema_name IN ARRAY ARRAY[{schemas}] LOOP
          IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = schema_name) THEN
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO shieldnet_backend', schema_name);
            EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO shieldnet_backend', schema_name);
            EXECUTE format('GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA %I TO shieldnet_backend', schema_name);
            EXECUTE format('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA %I TO shieldnet_backend', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE shieldnet_owner IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO shieldnet_backend', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE shieldnet_owner IN SCHEMA %I GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO shieldnet_backend', schema_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE shieldnet_owner IN SCHEMA %I GRANT EXECUTE ON FUNCTIONS TO shieldnet_backend', schema_name);
          END IF;
        END LOOP;
      END IF;
    END $$;
    """)


def downgrade() -> None:
    # Permissions are intentionally retained to avoid breaking the running API.
    pass

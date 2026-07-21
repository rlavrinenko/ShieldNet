"""create Discord guild tables
Revision ID: 0002_discord_guilds
Revises: 0001_core_auth
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='0002_discord_guilds'; down_revision='0001_core_auth'; branch_labels=None; depends_on=None

def upgrade():
    bind=op.get_bind()
    defs={'guild_status':('active','inactive','blocked','left','need_setup'),'bot_status':('online','offline','removed','error'),'membership_role':('admin','moderator'),'membership_status':('active','pending','revoked')}
    for n,v in defs.items(): postgresql.ENUM(*v,name=n,schema='discord').create(bind,checkfirst=True)
    gs=postgresql.ENUM(*defs['guild_status'],name='guild_status',schema='discord',create_type=False)
    bs=postgresql.ENUM(*defs['bot_status'],name='bot_status',schema='discord',create_type=False)
    mr=postgresql.ENUM(*defs['membership_role'],name='membership_role',schema='discord',create_type=False)
    ms=postgresql.ENUM(*defs['membership_status'],name='membership_status',schema='discord',create_type=False)
    op.create_table('guilds',sa.Column('guild_id',sa.BigInteger(),primary_key=True),sa.Column('name',sa.String(255),nullable=False),sa.Column('icon_url',sa.Text()),sa.Column('owner_discord_id',sa.BigInteger(),nullable=False),sa.Column('member_count',sa.Integer(),server_default='0',nullable=False),sa.Column('preferred_language',sa.String(16),server_default='uk',nullable=False),sa.Column('status',gs,server_default='need_setup',nullable=False),sa.Column('bot_status',bs,server_default='online',nullable=False),sa.Column('joined_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column('left_at',sa.DateTime(timezone=True)),sa.Column('last_sync_at',sa.DateTime(timezone=True)),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),schema='discord')
    op.create_table('guild_memberships',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('guild_id',sa.BigInteger(),nullable=False),sa.Column('user_id',postgresql.UUID(as_uuid=True)),sa.Column('discord_user_id',sa.BigInteger(),nullable=False),sa.Column('role',mr,nullable=False),sa.Column('status',ms,server_default='pending',nullable=False),sa.Column('created_by',postgresql.UUID(as_uuid=True)),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.ForeignKeyConstraint(['guild_id'],['discord.guilds.guild_id'],ondelete='CASCADE'),sa.ForeignKeyConstraint(['user_id'],['core.users.id'],ondelete='SET NULL'),sa.ForeignKeyConstraint(['created_by'],['core.users.id'],ondelete='SET NULL'),sa.UniqueConstraint('guild_id','discord_user_id',name='uq_discord_guild_membership_user'),schema='discord')
    op.create_index('ix_discord_guilds_owner','guilds',['owner_discord_id'],schema='discord')
    op.create_index('ix_discord_memberships_user_id','guild_memberships',['user_id'],schema='discord')

def downgrade():
    op.drop_table('guild_memberships',schema='discord'); op.drop_table('guilds',schema='discord')
    bind=op.get_bind()
    for n in ('membership_status','membership_role','bot_status','guild_status'): postgresql.ENUM(name=n,schema='discord').drop(bind,checkfirst=True)

"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('balance', sa.BigInteger(), nullable=True),
        sa.Column('client_seed', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )

    # Create bets table
    op.create_table('bets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('round_id', sa.String(length=255), nullable=False),
        sa.Column('bet_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('digits', sa.String(length=6), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Create provable_seeds table
    op.create_table('provable_seeds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('round_id', sa.String(length=255), nullable=False),
        sa.Column('commitment', sa.String(length=64), nullable=False),
        sa.Column('encrypted_seed', sa.Text(), nullable=False),
        sa.Column('revealed_seed_hash', sa.String(length=64), nullable=True),
        sa.Column('revealed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('period_tag', sa.String(length=50), nullable=True),
        sa.Column('drand_round', sa.String(length=50), nullable=True),
        sa.Column('client_seed_allowed', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('round_id')
    )

    # Create forced_actions table
    op.create_table('forced_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('requested_by', sa.BigInteger(), nullable=False),
        sa.Column('forced_value', sa.String(length=20), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=True),
        sa.Column('confirmations', sa.JSON(), nullable=True),
        sa.Column('required_confirmations', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('applied_round', sa.String(length=255), nullable=True),
        sa.Column('audit_ref', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create payouts table
    op.create_table('payouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tx_ref', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('round_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tx_ref'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.BigInteger(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target', sa.String(length=100), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create pot table
    op.create_table('pot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_bets_round_id', 'bets', ['round_id'])
    op.create_index('ix_bets_user_id', 'bets', ['user_id'])
    op.create_index('ix_provable_seeds_round_id', 'provable_seeds', ['round_id'])
    op.create_index('ix_forced_actions_chat_id', 'forced_actions', ['chat_id'])
    op.create_index('ix_payouts_tx_ref', 'payouts', ['tx_ref'])
    op.create_index('ix_payouts_user_id', 'payouts', ['user_id'])

def downgrade():
    op.drop_table('payouts')
    op.drop_table('audit_logs')
    op.drop_table('forced_actions')
    op.drop_table('provable_seeds')
    op.drop_table('bets')
    op.drop_table('pot')
    op.drop_table('users')

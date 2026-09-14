"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'payers',
        sa.Column('payer_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('payer_type', sa.String(50), nullable=True),
        sa.Column('edi_receiver_id', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('payer_id')
    )

    op.create_table(
        'providers',
        sa.Column('provider_id', sa.Integer(), nullable=False),
        sa.Column('npi', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('provider_id'),
        sa.UniqueConstraint('npi')
    )

    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )

    op.create_table(
        'patients',
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('mrn', sa.String(50), nullable=False),
        sa.Column('dob', sa.Date(), nullable=True),
        sa.Column('payer_id', sa.Integer(), nullable=True),
        sa.Column('member_id', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('patient_id'),
        sa.UniqueConstraint('mrn'),
        sa.ForeignKeyConstraint(['payer_id'], ['payers.payer_id'], )
    )

    op.create_table(
        'claims',
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=False),
        sa.Column('payer_id', sa.Integer(), nullable=False),
        sa.Column('date_of_service', sa.Date(), nullable=False),
        sa.Column('charge_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('paid_amount', sa.Numeric(12, 2), nullable=True, default=0),
        sa.Column('cpt_codes', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('icd10_codes', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('modifiers', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('status', sa.String(30), nullable=True, default='created'),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('edi_837_ref', sa.String(100), nullable=True),
        sa.Column('denial_predicted', sa.Boolean(), nullable=True, default=False),
        sa.Column('denial_probability', sa.Numeric(5, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('claim_id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.provider_id'], ),
        sa.ForeignKeyConstraint(['payer_id'], ['payers.payer_id'], )
    )
    op.create_index('idx_claims_status', 'claims', ['status'])
    op.create_index('idx_claims_payer', 'claims', ['payer_id'])
    op.create_index('idx_claims_dos', 'claims', ['date_of_service'])

    op.create_table(
        'denials',
        sa.Column('denial_id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('denial_code', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('denied_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('denial_date', sa.Date(), nullable=True),
        sa.Column('root_cause', sa.String(100), nullable=True),
        sa.Column('appeal_status', sa.String(30), nullable=True, default='not_started'),
        sa.Column('appeal_drafted_by_ai', sa.Boolean(), nullable=True, default=False),
        sa.PrimaryKeyConstraint('denial_id'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.claim_id'], )
    )

    op.create_table(
        'payments',
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('posted_date', sa.Date(), nullable=True),
        sa.Column('remittance_ref', sa.String(100), nullable=True),
        sa.Column('payer_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('payment_id'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.claim_id'], ),
        sa.ForeignKeyConstraint(['payer_id'], ['payers.payer_id'], )
    )

    op.create_table(
        'work_queues',
        sa.Column('queue_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('priority', sa.String(20), nullable=True, default='medium'),
        sa.Column('rule_definition', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('queue_id')
    )

    op.create_table(
        'claim_queue_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('queue_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.claim_id'], ),
        sa.ForeignKeyConstraint(['queue_id'], ['work_queues.queue_id'], )
    )

    op.create_table(
        'agent_runs',
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('input_payload', postgresql.JSONB(), nullable=True),
        sa.Column('output_payload', postgresql.JSONB(), nullable=True),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('hitl_required', sa.Boolean(), nullable=True, default=False),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('review_decision', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('run_id'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.claim_id'], )
    )


def downgrade() -> None:
    op.drop_table('agent_runs')
    op.drop_table('claim_queue_assignments')
    op.drop_table('work_queues')
    op.drop_table('payments')
    op.drop_table('denials')
    op.drop_index('idx_claims_dos', table_name='claims')
    op.drop_index('idx_claims_payer', table_name='claims')
    op.drop_index('idx_claims_status', table_name='claims')
    op.drop_table('claims')
    op.drop_table('patients')
    op.drop_table('users')
    op.drop_table('providers')
    op.drop_table('payers')
"""Add HR module tables

Revision ID: 002_hr_module
Revises: 001_pos_models
Create Date: 2025-12-02

BLQ HR Module: Employee, TimeEntry, PayrollRun, PaySlip
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_hr_module'
down_revision: Union[str, None] = '001_pos_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === EMPLOYEES TABLE ===
    op.create_table(
        'employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, unique=True),

        # Personal
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('nationality', sa.String(50), default='CH', nullable=False),
        sa.Column('ahv_number', sa.String(16), unique=True, nullable=False),

        # Contact
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('street', sa.String(255), nullable=False),
        sa.Column('postal_code', sa.String(10), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('canton', sa.String(2), default='LU', nullable=False),

        # Banking
        sa.Column('iban', sa.String(34), nullable=False),
        sa.Column('bank_name', sa.String(100), nullable=True),

        # Employment
        sa.Column('employee_number', sa.String(20), unique=True, nullable=False),
        sa.Column('contract_type', sa.String(20), default='fulltime', nullable=False),
        sa.Column('status', sa.String(20), default='probation', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('probation_end_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),

        # Compensation
        sa.Column('hours_per_week', sa.Numeric(5, 2), default=40.00, nullable=False),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('remote_days_per_week', sa.Integer(), default=0, nullable=False),
        sa.Column('remote_rate_multiplier', sa.Numeric(4, 2), default=0.80, nullable=False),

        # Benefits
        sa.Column('health_insurance_contribution', sa.Numeric(5, 2), default=0.00, nullable=False),
        sa.Column('health_insurance_active', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_quellensteuer', sa.Boolean(), default=False, nullable=False),
        sa.Column('quellensteuer_code', sa.String(10), nullable=True),
        sa.Column('bvg_insured', sa.Boolean(), default=True, nullable=False),
        sa.Column('bvg_contribution_rate', sa.Numeric(5, 4), default=0.0700, nullable=False),

        # Emergency
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(30), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_employees_user_id', 'employees', ['user_id'])
    op.create_index('ix_employees_employee_number', 'employees', ['employee_number'])

    # === PAYROLL RUNS TABLE ===
    op.create_table(
        'payroll_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('period_name', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), default='draft', nullable=False),

        # Workflow
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),

        # Totals
        sa.Column('total_employees', sa.Integer(), default=0, nullable=False),
        sa.Column('total_hours', sa.String(20), default='0.00', nullable=False),
        sa.Column('total_gross', sa.String(20), default='0.00', nullable=False),
        sa.Column('total_net', sa.String(20), default='0.00', nullable=False),
        sa.Column('total_employer_cost', sa.String(20), default='0.00', nullable=False),

        # MinIO paths
        sa.Column('csv_export_path', sa.String(500), nullable=True),
        sa.Column('pdf_archive_path', sa.String(500), nullable=True),
        sa.Column('audit_log_path', sa.String(500), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_payroll_runs_year_month', 'payroll_runs', ['year', 'month'])

    # === PAYSLIPS TABLE ===
    op.create_table(
        'payslips',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payroll_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payroll_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),

        # Period
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),

        # Employee snapshot
        sa.Column('employee_name', sa.String(200), nullable=False),
        sa.Column('employee_number', sa.String(20), nullable=False),
        sa.Column('ahv_number', sa.String(16), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False),

        # Hours
        sa.Column('regular_hours', sa.Numeric(6, 2), default=0, nullable=False),
        sa.Column('remote_hours', sa.Numeric(6, 2), default=0, nullable=False),
        sa.Column('holiday_hours', sa.Numeric(6, 2), default=0, nullable=False),
        sa.Column('sick_hours', sa.Numeric(6, 2), default=0, nullable=False),
        sa.Column('public_holiday_hours', sa.Numeric(6, 2), default=0, nullable=False),
        sa.Column('overtime_hours', sa.Numeric(6, 2), default=0, nullable=False),
        sa.Column('training_hours', sa.Numeric(6, 2), default=0, nullable=False),
        sa.Column('unpaid_hours', sa.Numeric(6, 2), default=0, nullable=False),
        sa.Column('total_hours', sa.Numeric(6, 2), default=0, nullable=False),

        # Gross components
        sa.Column('regular_pay', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('remote_pay', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('holiday_pay', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('sick_pay', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('public_holiday_pay', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('overtime_pay', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('training_pay', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('gross_salary', sa.Numeric(10, 2), nullable=False),

        # Deductions
        sa.Column('ahv_iv_eo', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('alv', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('alv2', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('bvg', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('uvg_nbu', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('ktg', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('quellensteuer', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('other_deductions', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('total_deductions', sa.Numeric(10, 2), nullable=False),

        # Additions
        sa.Column('kb_bonus', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('expense_reimbursement', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('other_additions', sa.Numeric(10, 2), default=0, nullable=False),

        # Net
        sa.Column('net_salary', sa.Numeric(10, 2), nullable=False),

        # Employer costs
        sa.Column('employer_ahv', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('employer_alv', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('employer_bvg', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('employer_uvg', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('employer_fak', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('employer_admin', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('total_employer_cost', sa.Numeric(10, 2), nullable=False),

        # Delivery
        sa.Column('pdf_generated', sa.Boolean(), default=False, nullable=False),
        sa.Column('pdf_path', sa.String(500), nullable=True),
        sa.Column('email_sent', sa.Boolean(), default=False, nullable=False),
        sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_payslips_payroll_run_id', 'payslips', ['payroll_run_id'])
    op.create_index('ix_payslips_employee_id', 'payslips', ['employee_id'])

    # === TIME ENTRIES TABLE ===
    op.create_table(
        'time_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),

        # Entry data
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('entry_type', sa.String(20), default='regular', nullable=False),
        sa.Column('hours', sa.Numeric(5, 2), nullable=False),
        sa.Column('start_time', sa.String(5), nullable=True),
        sa.Column('end_time', sa.String(5), nullable=True),
        sa.Column('break_minutes', sa.Integer(), default=0, nullable=False),

        # Approval
        sa.Column('status', sa.String(20), default='draft', nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),

        # Payslip link
        sa.Column('payslip_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payslips.id', ondelete='SET NULL'), nullable=True),

        # Description
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('kb_contribution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('kb_contributions.id', ondelete='SET NULL'), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_time_entries_employee_date', 'time_entries', ['employee_id', 'entry_date'])
    op.create_index('ix_time_entries_status', 'time_entries', ['status'])


def downgrade() -> None:
    op.drop_table('time_entries')
    op.drop_table('payslips')
    op.drop_table('payroll_runs')
    op.drop_table('employees')

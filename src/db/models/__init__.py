# File: app/db/models/__init__.py
# Purpose: Imports all SQLAlchemy models so they are registered with the Base metadata
# and exports all model names (including old aliases) for package-level imports.
from .base import Base
from .team_model import TeamModel
from .job_model import JobModel
from .artifact_model import ArtifactModel
from .message_tasks_model import MessageTaskModel
from .initializer_model import InitializerModel
from .pipeline_tasks_model import PipelineTaskModel
from .task_model import TaskModel
from .refresh_token_model import RefreshTokenModel
from .user_model import UserModel

# POS Models (Felix's Artemis Store)
from .product_model import ProductModel
from .transaction_model import TransactionModel, TransactionStatus, PaymentMethod
from .line_item_model import LineItemModel
from .store_settings_model import StoreSettingsModel

# CRACK Loyalty Models (Customer + KB Gamification)
from .customer_model import CustomerModel, CrackLevel, LoyaltyTier, PreferredContact
from .kb_contribution_model import KBContributionModel, KBStatus, KBCategory
from .credit_transaction_model import CreditTransactionModel, CreditTransactionType

# Sourcing System Models (Bestellungen)
from .supplier_model import SupplierModel
from .sourcing_request_model import SourcingRequestModel, SourcingNoteModel

# HR/Payroll Models (BLQ Module)
from .employee_model import EmployeeModel, ContractType, EmployeeStatus
from .time_entry_model import TimeEntryModel, EntryType, EntryStatus
from .payroll_run_model import PayrollRunModel, PayrollRunStatus
from .payslip_model import PaySlipModel

__all__ = [
    "Base",
    "UserModel",
    "TeamModel",
    "RefreshTokenModel",
    "JobModel",
    "TaskModel",
    "ArtifactModel",
    "MessageTaskModel",
    "PipelineTaskModel",
    "InitializerModel",
    # POS Models
    "ProductModel",
    "TransactionModel",
    "TransactionStatus",
    "PaymentMethod",
    "LineItemModel",
    "StoreSettingsModel",
    # CRACK Loyalty Models
    "CustomerModel",
    "CrackLevel",
    "LoyaltyTier",
    "PreferredContact",
    "KBContributionModel",
    "KBStatus",
    "KBCategory",
    "CreditTransactionModel",
    "CreditTransactionType",
    # Sourcing System Models
    "SupplierModel",
    "SourcingRequestModel",
    "SourcingNoteModel",
    # HR/Payroll Models
    "EmployeeModel",
    "ContractType",
    "EmployeeStatus",
    "TimeEntryModel",
    "EntryType",
    "EntryStatus",
    "PayrollRunModel",
    "PayrollRunStatus",
    "PaySlipModel",
]

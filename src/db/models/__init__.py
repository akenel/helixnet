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

# Shift & Session Management (BLQ: Handoff WIZARD)
from .shift_session_model import ShiftSessionModel, SessionStatus

# E2E Track & Trace Models (THE SPINE)
from .farm_model import FarmModel, FarmType
from .batch_model import BatchModel, BatchStatus, FreshnessRule
from .lab_test_model import LabTestModel, LabTestStatus, QualityGrade
from .traceable_item_model import TraceableItemModel, LifecycleStage, LocationType
from .trace_event_model import TraceEventModel, ActorType

# Equipment Supply Chain Models (YUKI & CHARLIE's Domain)
from .equipment_supplier_model import EquipmentSupplierModel, SupplierType
from .equipment_model import EquipmentModel, EquipmentType, EquipmentStatus
from .purchase_order_model import PurchaseOrderModel, POStatus
from .shipment_model import ShipmentModel, ShipmentType, ShipmentStatus
from .customs_clearance_model import CustomsClearanceModel, CustomsStatus
from .maintenance_event_model import MaintenanceEventModel, MaintenanceType, MaintenanceStatus
from .equipment_acquisition_model import EquipmentAcquisitionModel, AcquisitionType, AcquisitionStatus, UrgencyLevel

# Camper & Tour Service Management (Sebastino's Shop, Trapani)
from .camper_vehicle_model import CamperVehicleModel, VehicleType, VehicleStatus
from .camper_customer_model import CamperCustomerModel, CustomerLanguage
from .camper_service_job_model import CamperServiceJobModel, JobType, JobStatus
from .camper_quotation_model import CamperQuotationModel, QuotationStatus
from .camper_purchase_order_model import CamperPurchaseOrderModel, CamperPOStatus
from .camper_invoice_model import CamperInvoiceModel, PaymentStatus
from .camper_document_model import CamperDocumentModel

# ISOTTO Sport Print Shop (Via Buscaino, Trapani - since 1968)
from .isotto_customer_model import IsottoCustomerModel
from .isotto_order_model import IsottoOrderModel, ProductType, OrderStatus, ColorMode, DuplexMode, Lamination

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
    # Shift & Session
    "ShiftSessionModel",
    "SessionStatus",
    # E2E Track & Trace Models (THE SPINE)
    "FarmModel",
    "FarmType",
    "BatchModel",
    "BatchStatus",
    "FreshnessRule",
    "LabTestModel",
    "LabTestStatus",
    "QualityGrade",
    "TraceableItemModel",
    "LifecycleStage",
    "LocationType",
    "TraceEventModel",
    "ActorType",
    # Equipment Supply Chain Models (YUKI & CHARLIE)
    "EquipmentSupplierModel",
    "SupplierType",
    "EquipmentModel",
    "EquipmentType",
    "EquipmentStatus",
    "PurchaseOrderModel",
    "POStatus",
    "ShipmentModel",
    "ShipmentType",
    "ShipmentStatus",
    "CustomsClearanceModel",
    "CustomsStatus",
    "MaintenanceEventModel",
    "MaintenanceType",
    "MaintenanceStatus",
    # Equipment Acquisition (BUY vs LEASE vs RENT)
    "EquipmentAcquisitionModel",
    "AcquisitionType",
    "AcquisitionStatus",
    "UrgencyLevel",
    # Camper & Tour Service Management
    "CamperVehicleModel",
    "VehicleType",
    "VehicleStatus",
    "CamperCustomerModel",
    "CustomerLanguage",
    "CamperServiceJobModel",
    "JobType",
    "JobStatus",
    "CamperQuotationModel",
    "QuotationStatus",
    "CamperPurchaseOrderModel",
    "CamperPOStatus",
    "CamperInvoiceModel",
    "PaymentStatus",
    "CamperDocumentModel",
    # ISOTTO Sport Print Shop
    "IsottoCustomerModel",
    "IsottoOrderModel",
    "ProductType",
    "OrderStatus",
    "ColorMode",
    "DuplexMode",
    "Lamination",
]

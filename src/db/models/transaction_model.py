# File: src/db/models/transaction_model.py
"""
TransactionModel - Represents a sale/checkout session at Artemis POS.
Similar to JobModel - tracks the entire sale from scan to payment.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class TransactionStatus(enum.Enum):
    """Transaction lifecycle states"""
    OPEN = "open"              # Cart active, customer adding items
    PENDING = "pending"        # Awaiting payment
    COMPLETED = "completed"    # Payment successful
    CANCELLED = "cancelled"    # Transaction aborted
    REFUNDED = "refunded"      # Full refund issued


class PaymentMethod(enum.Enum):
    """Payment types for Felix's store"""
    CASH = "cash"
    VISA = "visa"
    DEBIT = "debit"
    TWINT = "twint"
    CRYPTO = "crypto"
    OTHER = "other"


class TransactionModel(Base):
    """
    Represents a complete sale transaction.
    Maps to 'Job' concept - one checkout session.
    """
    __tablename__ = 'transactions'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Transaction Number (Human-readable)
    transaction_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Sequential receipt number (e.g., 'TXN-20251126-0001')"
    )

    # Foreign Keys
    cashier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        comment="Staff member who processed the sale (Pam, Rafi, Michel)"
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=True,
        comment="Optional - for loyalty program customers"
    )

    # Transaction Status
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus),
        default=TransactionStatus.OPEN,
        nullable=False
    )

    # Payment Details
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        Enum(PaymentMethod),
        nullable=True,
        comment="How customer paid (null until checkout)"
    )

    # Financial Totals (in CHF)
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="Sum of all line items before discounts"
    )
    discount_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="Total discounts applied (loyalty, coupons)"
    )
    tax_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="VAT/tax (if applicable)"
    )
    total: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="Final amount charged to customer"
    )

    # Payment Processing
    amount_tendered: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Amount given by customer (cash only)"
    )
    change_given: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Change returned to customer (cash only)"
    )

    # Receipt Information
    receipt_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Printed receipt reference"
    )
    receipt_pdf_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="MinIO URL for stored receipt PDF"
    )

    # Notes and Metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Cashier notes, special requests, etc."
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When transaction started"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When payment was finalized"
    )

    # Relationships
    cashier: Mapped["UserModel"] = relationship(
        foreign_keys=[cashier_id],
        back_populates="cashier_transactions"
    )
    customer: Mapped["UserModel | None"] = relationship(
        foreign_keys=[customer_id],
        back_populates="customer_transactions"
    )
    line_items: Mapped[list["LineItemModel"]] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TransactionModel(number='{self.transaction_number}', total={self.total} CHF, status='{self.status.value}')>"

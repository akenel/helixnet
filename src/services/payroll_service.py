# File: src/services/payroll_service.py
"""
Swiss Payroll Calculation Engine - BLQ Module

"Be water, my friend" - Bruce Lee
"KICKIS: Keep It Clean, Keep It Simple" - BLQ Philosophy

Calculates:
- Gross salary from time entries
- Swiss social deductions (AHV, ALV, BVG, etc.)
- Employer contributions
- Net salary

Built for Canton Luzern rates, easily configurable.
"""
import logging
from datetime import datetime, timezone, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.db.models import (
    EmployeeModel,
    TimeEntryModel,
    PayrollRunModel,
    PaySlipModel,
    EntryStatus,
    EntryType,
    PayrollRunStatus,
    EmployeeStatus,
)

logger = logging.getLogger(__name__)


# ================================================================
# SWISS PAYROLL CONSTANTS (2024/2025)
# ================================================================

# AHV/IV/EO (Old age, disability, income replacement)
AHV_RATE_EMPLOYEE = Decimal("0.053")  # 5.3%
AHV_RATE_EMPLOYER = Decimal("0.053")  # 5.3%

# ALV (Unemployment insurance)
ALV_RATE_EMPLOYEE = Decimal("0.011")  # 1.1%
ALV_RATE_EMPLOYER = Decimal("0.011")  # 1.1%
ALV_MAX_SALARY_YEARLY = Decimal("148200")  # Max insured salary
ALV2_RATE = Decimal("0.005")  # 0.5% solidarity contribution above max

# UVG (Accident insurance)
UVG_BU_RATE = Decimal("0.0")  # Employer pays occupational accidents
UVG_NBU_RATE_EMPLOYEE = Decimal("0.0124")  # 1.24% non-occupational (if employee pays)

# FAK (Family compensation fund) - Canton Luzern
FAK_RATE_EMPLOYER = Decimal("0.012")  # 1.2%

# Admin fees
ADMIN_RATE_EMPLOYER = Decimal("0.002")  # 0.2%

# BVG (Pension) - Default rate, varies by age
BVG_DEFAULT_RATE = Decimal("0.07")  # 7% (split 50/50)

# Pay multipliers
OVERTIME_MULTIPLIER = Decimal("1.25")  # 125%
REMOTE_MULTIPLIER = Decimal("0.80")  # 80%
SICK_PAY_RATE = Decimal("1.00")  # 100% during sick leave (Swiss law)
HOLIDAY_PAY_RATE = Decimal("1.00")  # 100% paid vacation


def round_chf(amount: Decimal) -> Decimal:
    """Round to CHF 0.05 (Swiss rounding)."""
    return (amount * 20).quantize(Decimal("1"), rounding=ROUND_HALF_UP) / 20


class PayrollCalculator:
    """
    Swiss payroll calculation engine.

    Usage:
        calculator = PayrollCalculator(db_session)
        payroll_run = await calculator.create_payroll_run(2025, 1, creator_id)
        await calculator.calculate_all_payslips(payroll_run.id)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payroll_run(
        self,
        year: int,
        month: int,
        created_by_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> PayrollRunModel:
        """
        Create a new payroll run for a specific month.

        Args:
            year: Payroll year
            month: Payroll month (1-12)
            created_by_id: User who initiated the run
            notes: Optional notes

        Returns:
            Created PayrollRunModel
        """
        # Check for existing run
        existing = await self.db.execute(
            select(PayrollRunModel).where(
                and_(
                    PayrollRunModel.year == year,
                    PayrollRunModel.month == month,
                    PayrollRunModel.status != "closed"
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Payroll run for {year}-{month:02d} already exists")

        # Create run
        months_de = ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
                     "Juli", "August", "September", "Oktober", "November", "Dezember"]

        payroll_run = PayrollRunModel(
            year=year,
            month=month,
            period_name=f"{months_de[month]} {year}",
            status="draft",
            created_by_id=created_by_id,
            notes=notes,
        )

        self.db.add(payroll_run)
        await self.db.commit()
        await self.db.refresh(payroll_run)

        logger.info(f"Created payroll run: {payroll_run.period_name}")
        return payroll_run

    async def calculate_all_payslips(self, payroll_run_id: UUID) -> Dict:
        """
        Calculate payslips for all active employees.

        Args:
            payroll_run_id: The payroll run to process

        Returns:
            Summary of calculation results
        """
        # Get payroll run
        result = await self.db.execute(
            select(PayrollRunModel).where(PayrollRunModel.id == payroll_run_id)
        )
        payroll_run = result.scalar_one_or_none()

        if not payroll_run:
            raise ValueError("Payroll run not found")

        if payroll_run.status not in ["draft", "pending_review"]:
            raise ValueError(f"Cannot calculate payroll with status {payroll_run.status}")

        # Update status
        payroll_run.status = "calculating"
        await self.db.commit()

        # Get active employees
        result = await self.db.execute(
            select(EmployeeModel).where(
                EmployeeModel.status.in_(["probation", "active", "notice"])
            )
        )
        employees = result.scalars().all()

        # Calculate each payslip
        total_gross = Decimal("0")
        total_net = Decimal("0")
        total_employer_cost = Decimal("0")
        total_hours = Decimal("0")
        processed = 0
        errors = []

        for employee in employees:
            try:
                payslip = await self._calculate_employee_payslip(
                    employee, payroll_run
                )
                if payslip:
                    total_gross += payslip.gross_salary
                    total_net += payslip.net_salary
                    total_employer_cost += payslip.total_employer_cost
                    total_hours += payslip.total_hours
                    processed += 1
            except Exception as e:
                logger.error(f"Error calculating payslip for {employee.employee_number}: {e}")
                errors.append(f"{employee.employee_number}: {str(e)}")

        # Update payroll run totals
        payroll_run.total_employees = processed
        payroll_run.total_hours = str(total_hours)
        payroll_run.total_gross = str(total_gross)
        payroll_run.total_net = str(total_net)
        payroll_run.total_employer_cost = str(total_employer_cost)
        payroll_run.status = "pending_review"
        payroll_run.calculated_at = datetime.now(timezone.utc)

        await self.db.commit()

        logger.info(f"Payroll calculated: {processed} employees, CHF {total_gross} gross")

        return {
            "payroll_run_id": str(payroll_run_id),
            "period": payroll_run.period_name,
            "employees_processed": processed,
            "total_hours": float(total_hours),
            "total_gross": float(total_gross),
            "total_net": float(total_net),
            "total_employer_cost": float(total_employer_cost),
            "errors": errors if errors else None,
        }

    async def _calculate_employee_payslip(
        self,
        employee: EmployeeModel,
        payroll_run: PayrollRunModel
    ) -> Optional[PaySlipModel]:
        """
        Calculate payslip for a single employee.
        """
        year = payroll_run.year
        month = payroll_run.month

        # Get approved time entries for this month
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)

        result = await self.db.execute(
            select(TimeEntryModel).where(
                and_(
                    TimeEntryModel.employee_id == employee.id,
                    TimeEntryModel.entry_date >= month_start,
                    TimeEntryModel.entry_date < month_end,
                    TimeEntryModel.status == "approved"
                )
            )
        )
        entries = result.scalars().all()

        if not entries:
            logger.info(f"No approved entries for {employee.employee_number} in {year}-{month:02d}")
            return None

        # Aggregate hours by type
        hours = self._aggregate_hours(entries)

        # Calculate gross pay
        hourly_rate = employee.hourly_rate
        remote_rate = hourly_rate * (employee.remote_rate_multiplier or REMOTE_MULTIPLIER)
        overtime_rate = hourly_rate * OVERTIME_MULTIPLIER

        regular_pay = hours["regular"] * hourly_rate
        remote_pay = hours["remote"] * remote_rate
        holiday_pay = hours["holiday"] * hourly_rate
        sick_pay = hours["sick"] * hourly_rate
        public_holiday_pay = hours["public_holiday"] * hourly_rate
        overtime_pay = hours["overtime"] * overtime_rate
        training_pay = hours["training"] * hourly_rate

        gross_salary = (
            regular_pay + remote_pay + holiday_pay + sick_pay +
            public_holiday_pay + overtime_pay + training_pay
        )

        # Calculate deductions
        deductions = self._calculate_deductions(gross_salary, employee)

        # Calculate employer costs
        employer_costs = self._calculate_employer_costs(gross_salary, employee)

        # KB bonus (from CRACK contributions - placeholder)
        kb_bonus = Decimal("0")  # TODO: Query KB contributions for this month

        # Net salary
        net_salary = gross_salary - deductions["total"] + kb_bonus

        # Total employer cost
        total_employer_cost = gross_salary + employer_costs["total"]

        # Create payslip
        payslip = PaySlipModel(
            payroll_run_id=payroll_run.id,
            employee_id=employee.id,
            year=year,
            month=month,

            # Employee snapshot
            employee_name=f"{employee.first_name} {employee.last_name}",
            employee_number=employee.employee_number,
            ahv_number=employee.ahv_number,
            hourly_rate=hourly_rate,

            # Hours
            regular_hours=hours["regular"],
            remote_hours=hours["remote"],
            holiday_hours=hours["holiday"],
            sick_hours=hours["sick"],
            public_holiday_hours=hours["public_holiday"],
            overtime_hours=hours["overtime"],
            training_hours=hours["training"],
            unpaid_hours=hours["unpaid"],
            total_hours=hours["total"],

            # Gross
            regular_pay=round_chf(regular_pay),
            remote_pay=round_chf(remote_pay),
            holiday_pay=round_chf(holiday_pay),
            sick_pay=round_chf(sick_pay),
            public_holiday_pay=round_chf(public_holiday_pay),
            overtime_pay=round_chf(overtime_pay),
            training_pay=round_chf(training_pay),
            gross_salary=round_chf(gross_salary),

            # Deductions
            ahv_iv_eo=round_chf(deductions["ahv"]),
            alv=round_chf(deductions["alv"]),
            alv2=round_chf(deductions["alv2"]),
            bvg=round_chf(deductions["bvg"]),
            uvg_nbu=round_chf(deductions["nbu"]),
            ktg=Decimal("0"),
            quellensteuer=round_chf(deductions["quellensteuer"]),
            other_deductions=Decimal("0"),
            total_deductions=round_chf(deductions["total"]),

            # Additions
            kb_bonus=kb_bonus,
            expense_reimbursement=Decimal("0"),
            other_additions=Decimal("0"),

            # Net
            net_salary=round_chf(net_salary),

            # Employer costs
            employer_ahv=round_chf(employer_costs["ahv"]),
            employer_alv=round_chf(employer_costs["alv"]),
            employer_bvg=round_chf(employer_costs["bvg"]),
            employer_uvg=round_chf(employer_costs["uvg"]),
            employer_fak=round_chf(employer_costs["fak"]),
            employer_admin=round_chf(employer_costs["admin"]),
            total_employer_cost=round_chf(total_employer_cost),
        )

        self.db.add(payslip)

        # Mark time entries as paid
        for entry in entries:
            entry.status = "paid"
            entry.payslip_id = payslip.id

        await self.db.commit()
        await self.db.refresh(payslip)

        logger.info(f"Payslip created: {employee.employee_number} - CHF {net_salary} net")
        return payslip

    def _aggregate_hours(self, entries: List[TimeEntryModel]) -> Dict[str, Decimal]:
        """Aggregate hours by entry type."""
        hours = {
            "regular": Decimal("0"),
            "remote": Decimal("0"),
            "holiday": Decimal("0"),
            "sick": Decimal("0"),
            "public_holiday": Decimal("0"),
            "overtime": Decimal("0"),
            "training": Decimal("0"),
            "unpaid": Decimal("0"),
            "total": Decimal("0"),
        }

        for entry in entries:
            entry_type = entry.entry_type
            if entry_type in hours:
                hours[entry_type] += entry.hours
            else:
                hours["regular"] += entry.hours

            # Total excludes unpaid
            if entry_type != "unpaid":
                hours["total"] += entry.hours

        return hours

    def _calculate_deductions(
        self,
        gross_salary: Decimal,
        employee: EmployeeModel
    ) -> Dict[str, Decimal]:
        """Calculate all employee deductions."""
        deductions = {
            "ahv": Decimal("0"),
            "alv": Decimal("0"),
            "alv2": Decimal("0"),
            "bvg": Decimal("0"),
            "nbu": Decimal("0"),
            "quellensteuer": Decimal("0"),
            "total": Decimal("0"),
        }

        # AHV/IV/EO - 5.3%
        deductions["ahv"] = gross_salary * AHV_RATE_EMPLOYEE

        # ALV - 1.1% (up to max salary)
        monthly_max = ALV_MAX_SALARY_YEARLY / 12
        alv_base = min(gross_salary, monthly_max)
        deductions["alv"] = alv_base * ALV_RATE_EMPLOYEE

        # ALV2 - 0.5% solidarity (above max)
        if gross_salary > monthly_max:
            deductions["alv2"] = (gross_salary - monthly_max) * ALV2_RATE

        # BVG - Pension (if insured)
        if employee.bvg_insured:
            bvg_rate = employee.bvg_contribution_rate or BVG_DEFAULT_RATE
            # Employee pays half
            deductions["bvg"] = gross_salary * (bvg_rate / 2)

        # NBU - Non-occupational accident (optional)
        # Some companies have employee pay this
        deductions["nbu"] = Decimal("0")  # Default: employer pays

        # Quellensteuer (withholding tax for foreigners)
        if employee.is_quellensteuer and employee.quellensteuer_code:
            # Simplified: use a flat rate based on code
            # In reality, this uses canton-specific tables
            # Example: A0 = ~10%, B1 = ~15%, C2 = ~20%
            code = employee.quellensteuer_code.upper()
            if code.startswith("A"):
                rate = Decimal("0.10")
            elif code.startswith("B"):
                rate = Decimal("0.15")
            elif code.startswith("C"):
                rate = Decimal("0.20")
            else:
                rate = Decimal("0.12")  # Default
            deductions["quellensteuer"] = gross_salary * rate

        # Total
        deductions["total"] = sum(deductions.values())

        return deductions

    def _calculate_employer_costs(
        self,
        gross_salary: Decimal,
        employee: EmployeeModel
    ) -> Dict[str, Decimal]:
        """Calculate all employer contributions."""
        costs = {
            "ahv": Decimal("0"),
            "alv": Decimal("0"),
            "bvg": Decimal("0"),
            "uvg": Decimal("0"),
            "fak": Decimal("0"),
            "admin": Decimal("0"),
            "total": Decimal("0"),
        }

        # AHV/IV/EO - 5.3%
        costs["ahv"] = gross_salary * AHV_RATE_EMPLOYER

        # ALV - 1.1% (up to max salary)
        monthly_max = ALV_MAX_SALARY_YEARLY / 12
        alv_base = min(gross_salary, monthly_max)
        costs["alv"] = alv_base * ALV_RATE_EMPLOYER

        # BVG - Employer pays half
        if employee.bvg_insured:
            bvg_rate = employee.bvg_contribution_rate or BVG_DEFAULT_RATE
            costs["bvg"] = gross_salary * (bvg_rate / 2)

        # UVG - Accident insurance (employer pays BU, often NBU too)
        # Simplified flat rate
        costs["uvg"] = gross_salary * Decimal("0.015")  # ~1.5%

        # FAK - Family compensation fund (Canton Luzern)
        costs["fak"] = gross_salary * FAK_RATE_EMPLOYER

        # Admin costs
        costs["admin"] = gross_salary * ADMIN_RATE_EMPLOYER

        # Total
        costs["total"] = sum(costs.values())

        return costs

    async def approve_payroll_run(
        self,
        payroll_run_id: UUID,
        approved_by_id: UUID
    ) -> PayrollRunModel:
        """
        Approve a calculated payroll run.
        """
        result = await self.db.execute(
            select(PayrollRunModel).where(PayrollRunModel.id == payroll_run_id)
        )
        payroll_run = result.scalar_one_or_none()

        if not payroll_run:
            raise ValueError("Payroll run not found")

        if payroll_run.status != "pending_review":
            raise ValueError(f"Cannot approve payroll with status {payroll_run.status}")

        payroll_run.status = "approved"
        payroll_run.approved_by_id = approved_by_id
        payroll_run.approved_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(payroll_run)

        logger.info(f"Payroll approved: {payroll_run.period_name}")
        return payroll_run

    async def mark_payroll_paid(
        self,
        payroll_run_id: UUID
    ) -> PayrollRunModel:
        """
        Mark payroll as paid (after bank transfer).
        """
        result = await self.db.execute(
            select(PayrollRunModel).where(PayrollRunModel.id == payroll_run_id)
        )
        payroll_run = result.scalar_one_or_none()

        if not payroll_run:
            raise ValueError("Payroll run not found")

        if payroll_run.status != "approved":
            raise ValueError(f"Cannot mark as paid with status {payroll_run.status}")

        payroll_run.status = "paid"
        payroll_run.paid_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(payroll_run)

        logger.info(f"Payroll marked paid: {payroll_run.period_name}")
        return payroll_run

    async def get_payroll_summary(self, payroll_run_id: UUID) -> Dict:
        """
        Get detailed summary of a payroll run.
        """
        result = await self.db.execute(
            select(PayrollRunModel).where(PayrollRunModel.id == payroll_run_id)
        )
        payroll_run = result.scalar_one_or_none()

        if not payroll_run:
            raise ValueError("Payroll run not found")

        # Get all payslips
        result = await self.db.execute(
            select(PaySlipModel).where(PaySlipModel.payroll_run_id == payroll_run_id)
        )
        payslips = result.scalars().all()

        return {
            "payroll_run": {
                "id": str(payroll_run.id),
                "period": payroll_run.period_name,
                "status": payroll_run.status,
                "total_employees": payroll_run.total_employees,
                "total_gross": payroll_run.total_gross,
                "total_net": payroll_run.total_net,
                "total_employer_cost": payroll_run.total_employer_cost,
                "calculated_at": payroll_run.calculated_at.isoformat() if payroll_run.calculated_at else None,
                "approved_at": payroll_run.approved_at.isoformat() if payroll_run.approved_at else None,
                "paid_at": payroll_run.paid_at.isoformat() if payroll_run.paid_at else None,
            },
            "payslips": [
                {
                    "employee_name": p.employee_name,
                    "employee_number": p.employee_number,
                    "total_hours": float(p.total_hours),
                    "gross_salary": float(p.gross_salary),
                    "total_deductions": float(p.total_deductions),
                    "net_salary": float(p.net_salary),
                    "employer_cost": float(p.total_employer_cost),
                }
                for p in payslips
            ],
        }

# File: src/routes/pets_router.py
"""
HelixPETS API Router
"Be water, my friend." - Bruce Lee
"Be furry, my friend." - Michel the Animal Whisperer

Michel's pet wash station at the Stans bookstore.
Where books meet barks. Where VIVI does therapy and Michel does magic.

1291: One page for Switzerland
2025: One router for pets
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

from src.db.database import get_db
from src.db.models.pet_model import (
    PetModel, PetWashAppointment, PetSpecies, PetSize,
    WashServiceType, AppointmentStatus, get_service_price
)
from src.schemas.pet_schema import (
    PetCreate, PetUpdate, PetRead,
    AppointmentCreate, AppointmentUpdate, AppointmentRead, AppointmentWithPet,
    PetWashStats, ServicePriceRequest, ServicePriceResponse,
    PetSpeciesEnum, PetSizeEnum, WashServiceTypeEnum, AppointmentStatusEnum
)

router = APIRouter(prefix="/api/v1/pets", tags=["Pet Wash Station"])


# ================================================================
# PET CRUD - Michel's Registry
# ================================================================

@router.post("/", response_model=PetRead, status_code=201)
async def register_pet(
    pet: PetCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new pet.
    Michel remembers every pet in Stans by name.
    """
    db_pet = PetModel(
        name=pet.name,
        species=PetSpecies[pet.species.name] if pet.species else PetSpecies.DOG,
        breed=pet.breed,
        color=pet.color,
        size=PetSize[pet.size.name] if pet.size else PetSize.MEDIUM,
        birth_date=pet.birth_date,
        weight_kg=pet.weight_kg,
        microchip_id=pet.microchip_id,
        allergies=pet.allergies,
        medical_notes=pet.medical_notes,
        temperament=pet.temperament,
        special_instructions=pet.special_instructions,
        owner_name=pet.owner_name,
        owner_phone=pet.owner_phone,
        photo_url=pet.photo_url,
        customer_id=pet.customer_id
    )
    db.add(db_pet)
    await db.commit()
    await db.refresh(db_pet)
    return db_pet


@router.get("/", response_model=list[PetRead])
async def list_pets(
    species: Optional[PetSpeciesEnum] = None,
    owner_name: Optional[str] = None,
    search: Optional[str] = None,
    active_only: bool = True,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List all registered pets.
    Michel's little black book of furry friends.
    """
    query = select(PetModel)

    if active_only:
        query = query.where(PetModel.is_active == True)
    if species:
        query = query.where(PetModel.species == PetSpecies[species.name])
    if owner_name:
        query = query.where(PetModel.owner_name.ilike(f"%{owner_name}%"))
    if search:
        query = query.where(
            (PetModel.name.ilike(f"%{search}%")) |
            (PetModel.owner_name.ilike(f"%{search}%")) |
            (PetModel.breed.ilike(f"%{search}%"))
        )

    query = query.order_by(PetModel.name)
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/microchip/{microchip_id}", response_model=PetRead)
async def get_pet_by_microchip(
    microchip_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Find a pet by microchip ID.
    The pet's unique identifier - like a barcode for fur babies.
    """
    query = select(PetModel).where(PetModel.microchip_id == microchip_id)
    result = await db.execute(query)
    pet = result.scalar_one_or_none()

    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@router.get("/{pet_id}", response_model=PetRead)
async def get_pet(
    pet_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a pet by ID"""
    query = select(PetModel).where(PetModel.id == pet_id)
    result = await db.execute(query)
    pet = result.scalar_one_or_none()

    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@router.put("/{pet_id}", response_model=PetRead)
async def update_pet(
    pet_id: UUID,
    pet_update: PetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a pet's information"""
    query = select(PetModel).where(PetModel.id == pet_id)
    result = await db.execute(query)
    pet = result.scalar_one_or_none()

    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    update_data = pet_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'species' and value:
            value = PetSpecies[value.name]
        if field == 'size' and value:
            value = PetSize[value.name]
        setattr(pet, field, value)

    await db.commit()
    await db.refresh(pet)
    return pet


@router.delete("/{pet_id}", status_code=204)
async def deactivate_pet(
    pet_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a pet (soft delete).
    Pets are never truly deleted - they live on in our hearts.
    """
    query = select(PetModel).where(PetModel.id == pet_id)
    result = await db.execute(query)
    pet = result.scalar_one_or_none()

    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    pet.is_active = False
    await db.commit()


# ================================================================
# APPOINTMENTS - Michel's Calendar
# ================================================================

@router.post("/appointments", response_model=AppointmentRead, status_code=201)
async def book_appointment(
    appointment: AppointmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Book a wash appointment.
    Michel's calendar fills up fast!
    """
    # Check pet exists
    pet_query = select(PetModel).where(PetModel.id == appointment.pet_id)
    pet_result = await db.execute(pet_query)
    pet = pet_result.scalar_one_or_none()

    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    # Auto-calculate price if not provided
    price = appointment.price
    if price is None:
        service = WashServiceType[appointment.service_type.name]
        size = pet.size
        price = get_service_price(service, size)

    db_appointment = PetWashAppointment(
        pet_id=appointment.pet_id,
        service_type=WashServiceType[appointment.service_type.name],
        scheduled_at=appointment.scheduled_at,
        duration_minutes=appointment.duration_minutes,
        price=price,
        notes=appointment.notes
    )
    db.add(db_appointment)
    await db.commit()
    await db.refresh(db_appointment)
    return db_appointment


@router.get("/appointments/today", response_model=list[AppointmentRead])
async def get_today_appointments(
    db: AsyncSession = Depends(get_db)
):
    """
    Get today's appointments.
    Michel's morning briefing.
    """
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    query = select(PetWashAppointment).where(
        and_(
            PetWashAppointment.scheduled_at >= start_of_day,
            PetWashAppointment.scheduled_at < end_of_day,
            PetWashAppointment.status != AppointmentStatus.CANCELLED
        )
    ).order_by(PetWashAppointment.scheduled_at)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/appointments/upcoming", response_model=list[AppointmentRead])
async def get_upcoming_appointments(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db)
):
    """
    Get upcoming appointments.
    Plan ahead like Michel does.
    """
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=days)

    query = select(PetWashAppointment).where(
        and_(
            PetWashAppointment.scheduled_at >= now,
            PetWashAppointment.scheduled_at <= end_date,
            PetWashAppointment.status.in_([
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CHECKED_IN
            ])
        )
    ).order_by(PetWashAppointment.scheduled_at)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/appointments/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get an appointment by ID"""
    query = select(PetWashAppointment).where(
        PetWashAppointment.id == appointment_id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.put("/appointments/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: UUID,
    appointment_update: AppointmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an appointment"""
    query = select(PetWashAppointment).where(
        PetWashAppointment.id == appointment_id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_data = appointment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'service_type' and value:
            value = WashServiceType[value.name]
        if field == 'status' and value:
            value = AppointmentStatus[value.name]
            # Set completed_at when marking as completed
            if value == AppointmentStatus.COMPLETED:
                appointment.completed_at = datetime.now(timezone.utc)
        setattr(appointment, field, value)

    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.post("/appointments/{appointment_id}/check-in", response_model=AppointmentRead)
async def check_in_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Check in a pet for their appointment"""
    query = select(PetWashAppointment).where(
        PetWashAppointment.id == appointment_id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(status_code=400, detail="Appointment cannot be checked in")

    appointment.status = AppointmentStatus.CHECKED_IN
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.post("/appointments/{appointment_id}/start", response_model=AppointmentRead)
async def start_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Start working on a pet"""
    query = select(PetWashAppointment).where(
        PetWashAppointment.id == appointment_id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = AppointmentStatus.IN_PROGRESS
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.post("/appointments/{appointment_id}/complete", response_model=AppointmentRead)
async def complete_appointment(
    appointment_id: UUID,
    groomer_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Complete an appointment"""
    query = select(PetWashAppointment).where(
        PetWashAppointment.id == appointment_id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = AppointmentStatus.COMPLETED
    appointment.completed_at = datetime.now(timezone.utc)
    if groomer_notes:
        appointment.groomer_notes = groomer_notes

    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.delete("/appointments/{appointment_id}", status_code=204)
async def cancel_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Cancel an appointment"""
    query = select(PetWashAppointment).where(
        PetWashAppointment.id == appointment_id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = AppointmentStatus.CANCELLED
    await db.commit()


# ================================================================
# PRICING - Michel's Rate Card
# ================================================================

@router.post("/pricing/calculate", response_model=ServicePriceResponse)
async def calculate_service_price(
    request: ServicePriceRequest
):
    """
    Calculate service price based on service type and pet size.
    Fair pricing for Stans.
    """
    service = WashServiceType[request.service_type.name]
    size = PetSize[request.size.name]
    price = get_service_price(service, size)

    # Duration estimates
    duration_map = {
        WashServiceType.BASIC_WASH: 30,
        WashServiceType.FULL_GROOM: 60,
        WashServiceType.NAIL_TRIM: 15,
        WashServiceType.TEETH_CLEAN: 20,
        WashServiceType.FLEA_TREATMENT: 45,
        WashServiceType.DELUXE_SPA: 90,
    }

    return ServicePriceResponse(
        service_type=request.service_type,
        size=request.size,
        price_chf=price,
        duration_minutes=duration_map.get(service, 30)
    )


# ================================================================
# STATS - For Michel and Angel
# ================================================================

@router.get("/stats/overview", response_model=PetWashStats)
async def get_pet_wash_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Pet wash station statistics.
    What Michel wants to see at the start of each day.
    """
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())

    # Total pets
    total_pets_result = await db.execute(
        select(func.count(PetModel.id)).where(PetModel.is_active == True)
    )
    total_pets = total_pets_result.scalar() or 0

    # Total appointments
    total_appts_result = await db.execute(
        select(func.count(PetWashAppointment.id))
    )
    total_appointments = total_appts_result.scalar() or 0

    # Today's appointments
    today_appts_result = await db.execute(
        select(func.count(PetWashAppointment.id)).where(
            and_(
                PetWashAppointment.scheduled_at >= start_of_day,
                PetWashAppointment.scheduled_at < start_of_day + timedelta(days=1),
                PetWashAppointment.status != AppointmentStatus.CANCELLED
            )
        )
    )
    appointments_today = today_appts_result.scalar() or 0

    # This week's appointments
    week_appts_result = await db.execute(
        select(func.count(PetWashAppointment.id)).where(
            and_(
                PetWashAppointment.scheduled_at >= start_of_week,
                PetWashAppointment.scheduled_at < start_of_week + timedelta(days=7),
                PetWashAppointment.status != AppointmentStatus.CANCELLED
            )
        )
    )
    appointments_this_week = week_appts_result.scalar() or 0

    # Revenue today
    today_revenue_result = await db.execute(
        select(func.sum(PetWashAppointment.price)).where(
            and_(
                PetWashAppointment.scheduled_at >= start_of_day,
                PetWashAppointment.scheduled_at < start_of_day + timedelta(days=1),
                PetWashAppointment.status == AppointmentStatus.COMPLETED,
                PetWashAppointment.paid == True
            )
        )
    )
    revenue_today = float(today_revenue_result.scalar() or 0)

    # Revenue this week
    week_revenue_result = await db.execute(
        select(func.sum(PetWashAppointment.price)).where(
            and_(
                PetWashAppointment.scheduled_at >= start_of_week,
                PetWashAppointment.scheduled_at < start_of_week + timedelta(days=7),
                PetWashAppointment.status == AppointmentStatus.COMPLETED,
                PetWashAppointment.paid == True
            )
        )
    )
    revenue_this_week = float(week_revenue_result.scalar() or 0)

    # Pets by species
    species_result = await db.execute(
        select(PetModel.species, func.count(PetModel.id))
        .where(PetModel.is_active == True)
        .group_by(PetModel.species)
    )
    pets_by_species = {str(row[0].value): row[1] for row in species_result.all()}

    # Popular services
    services_result = await db.execute(
        select(PetWashAppointment.service_type, func.count(PetWashAppointment.id))
        .group_by(PetWashAppointment.service_type)
        .order_by(func.count(PetWashAppointment.id).desc())
        .limit(5)
    )
    popular_services = [
        {"service": str(row[0].value), "count": row[1]}
        for row in services_result.all()
    ]

    # Upcoming appointments (next 5)
    upcoming_result = await db.execute(
        select(PetWashAppointment)
        .where(
            and_(
                PetWashAppointment.scheduled_at >= now,
                PetWashAppointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CHECKED_IN
                ])
            )
        )
        .order_by(PetWashAppointment.scheduled_at)
        .limit(5)
    )
    upcoming_appointments = []

    return PetWashStats(
        total_pets=total_pets,
        total_appointments=total_appointments,
        appointments_today=appointments_today,
        appointments_this_week=appointments_this_week,
        revenue_today=revenue_today,
        revenue_this_week=revenue_this_week,
        pets_by_species=pets_by_species,
        popular_services=popular_services,
        upcoming_appointments=upcoming_appointments
    )


# ================================================================
# PET HISTORY - For Michel
# ================================================================

@router.get("/{pet_id}/history", response_model=list[AppointmentRead])
async def get_pet_history(
    pet_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a pet's appointment history.
    Michel remembers everything, but now Helix does too.
    """
    # Check pet exists
    pet_query = select(PetModel).where(PetModel.id == pet_id)
    pet_result = await db.execute(pet_query)
    pet = pet_result.scalar_one_or_none()

    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    # Get appointment history
    query = select(PetWashAppointment).where(
        PetWashAppointment.pet_id == pet_id
    ).order_by(PetWashAppointment.scheduled_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

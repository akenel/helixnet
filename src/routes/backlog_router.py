# File: src/routes/backlog_router.py
# Purpose: Unified Backlog -- API + HTML routes
# Auth: Keycloak RBAC via camper-qa-tester / camper-manager / camper-admin

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import get_db_session
from src.db.models.backlog_model import (
    BacklogItemModel, BacklogItemType, BacklogStatus, BacklogPriority,
    BacklogActivityModel, BacklogActivityType,
)
from src.schemas.backlog_schema import (
    BacklogItemCreate, BacklogItemUpdate, BacklogItemRead,
    BacklogActivityRead, BacklogSummary,
)
from src.core.keycloak_auth import require_roles


def require_backlog_access():
    """Backlog access -- same roles as QA dashboard."""
    return require_roles(["camper-qa-tester", "camper-manager", "camper-admin"])


logger = logging.getLogger("helix.backlog_router")

# ================================================================
# Router Setup
# ================================================================
router = APIRouter(prefix="/api/v1/backlog", tags=["Backlog - Unified Board"])
html_router = APIRouter(tags=["Backlog - Web UI"])

templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ================================================================
# API: Summary
# ================================================================
@router.get("/summary", response_model=BacklogSummary)
async def get_summary(
    current_user: dict = Depends(require_backlog_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Backlog overview counts by status, type, priority."""
    # Counts by status
    status_result = await db.execute(
        select(
            BacklogItemModel.status,
            func.count().label("cnt"),
        ).group_by(BacklogItemModel.status)
    )
    status_counts = {row.status.value: row.cnt for row in status_result}

    # Counts by type
    type_result = await db.execute(
        select(
            BacklogItemModel.item_type,
            func.count().label("cnt"),
        ).group_by(BacklogItemModel.item_type)
    )
    type_counts = {row.item_type.value: row.cnt for row in type_result}

    # Counts by priority
    priority_result = await db.execute(
        select(
            BacklogItemModel.priority,
            func.count().label("cnt"),
        ).group_by(BacklogItemModel.priority)
    )
    priority_counts = {row.priority.value: row.cnt for row in priority_result}

    total = sum(status_counts.values())

    return BacklogSummary(
        total=total,
        pending=status_counts.get("pending", 0),
        in_progress=status_counts.get("in_progress", 0),
        blocked=status_counts.get("blocked", 0),
        done=status_counts.get("done", 0),
        archived=status_counts.get("archived", 0),
        by_type=type_counts,
        by_priority=priority_counts,
    )


# ================================================================
# API: List Items
# ================================================================
@router.get("/items", response_model=list[BacklogItemRead])
async def list_items(
    item_type: str | None = None,
    status_filter: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    current_user: dict = Depends(require_backlog_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """List backlog items with optional filters."""
    query = select(BacklogItemModel)

    if item_type:
        try:
            t = BacklogItemType(item_type)
            query = query.where(BacklogItemModel.item_type == t)
        except ValueError:
            pass

    if status_filter:
        try:
            s = BacklogStatus(status_filter)
            query = query.where(BacklogItemModel.status == s)
        except ValueError:
            pass

    if priority:
        try:
            p = BacklogPriority(priority)
            query = query.where(BacklogItemModel.priority == p)
        except ValueError:
            pass

    if assigned_to:
        query = query.where(BacklogItemModel.assigned_to == assigned_to)

    query = query.order_by(BacklogItemModel.item_number)
    result = await db.execute(query)
    return result.scalars().all()


# ================================================================
# API: Create Item
# ================================================================
@router.post("/items", response_model=BacklogItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: BacklogItemCreate,
    current_user: dict = Depends(require_backlog_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new backlog item."""
    # Auto-assign next item number
    max_num = await db.execute(
        select(func.coalesce(func.max(BacklogItemModel.item_number), 0))
    )
    next_number = max_num.scalar() + 1

    new_item = BacklogItemModel(
        item_number=next_number,
        title=item.title,
        description=item.description,
        item_type=item.item_type,
        priority=item.priority,
        assigned_to=item.assigned_to,
        due_date=item.due_date,
        estimated_hours=item.estimated_hours,
        tags=item.tags,
        created_by=item.created_by,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    logger.info(f"BL-{next_number:03d} created: {item.title}")
    return new_item


# ================================================================
# API: Get Single Item
# ================================================================
@router.get("/items/{item_id}", response_model=BacklogItemRead)
async def get_item(
    item_id: UUID,
    current_user: dict = Depends(require_backlog_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a single backlog item."""
    result = await db.execute(
        select(BacklogItemModel).where(BacklogItemModel.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    return item


# ================================================================
# API: Update Item
# ================================================================
@router.put("/items/{item_id}", response_model=BacklogItemRead)
async def update_item(
    item_id: UUID,
    update: BacklogItemUpdate,
    current_user: dict = Depends(require_backlog_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a backlog item -- auto-creates activity log entries for tracked changes."""
    result = await db.execute(
        select(BacklogItemModel).where(BacklogItemModel.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Backlog item not found")

    actor = update.actor or "Angel"
    activities = []

    # Track status change
    if update.status is not None and update.status != item.status:
        activities.append(BacklogActivityModel(
            item_id=item.id,
            activity_type=BacklogActivityType.STATUS_CHANGE,
            actor=actor,
            old_value=item.status.value,
            new_value=update.status.value,
        ))
        item.status = update.status

    # Track priority change
    if update.priority is not None and update.priority != item.priority:
        activities.append(BacklogActivityModel(
            item_id=item.id,
            activity_type=BacklogActivityType.PRIORITY_CHANGE,
            actor=actor,
            old_value=item.priority.value,
            new_value=update.priority.value,
        ))
        item.priority = update.priority

    # Track assignment change
    if update.assigned_to is not None and update.assigned_to != (item.assigned_to or ""):
        new_assignee = update.assigned_to if update.assigned_to else None
        activities.append(BacklogActivityModel(
            item_id=item.id,
            activity_type=BacklogActivityType.ASSIGNED,
            actor=actor,
            old_value=item.assigned_to,
            new_value=new_assignee,
        ))
        item.assigned_to = new_assignee

    # Comment
    if update.comment:
        activities.append(BacklogActivityModel(
            item_id=item.id,
            activity_type=BacklogActivityType.COMMENT,
            actor=actor,
            comment=update.comment,
        ))

    # Apply remaining field updates (not tracked in activity log)
    if update.title is not None:
        item.title = update.title
    if update.description is not None:
        item.description = update.description
    if update.item_type is not None:
        item.item_type = update.item_type
    if update.due_date is not None:
        item.due_date = update.due_date
    if update.estimated_hours is not None:
        item.estimated_hours = update.estimated_hours
    if update.blocked_reason is not None:
        item.blocked_reason = update.blocked_reason if update.blocked_reason else None
    if update.tags is not None:
        item.tags = update.tags if update.tags else None

    item.updated_at = datetime.now(timezone.utc)

    for activity in activities:
        db.add(activity)

    await db.commit()
    await db.refresh(item)

    if activities:
        logger.info(f"BL-{item.item_number:03d} updated by {actor}: {len(activities)} activity entries")

    return item


# ================================================================
# API: Delete Item (soft delete -> archived)
# ================================================================
@router.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
async def delete_item(
    item_id: UUID,
    current_user: dict = Depends(require_backlog_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Soft delete a backlog item (set status=archived)."""
    result = await db.execute(
        select(BacklogItemModel).where(BacklogItemModel.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Backlog item not found")

    old_status = item.status.value
    item.status = BacklogStatus.ARCHIVED
    item.updated_at = datetime.now(timezone.utc)

    db.add(BacklogActivityModel(
        item_id=item.id,
        activity_type=BacklogActivityType.STATUS_CHANGE,
        actor="System",
        old_value=old_status,
        new_value=BacklogStatus.ARCHIVED.value,
    ))

    await db.commit()
    logger.info(f"BL-{item.item_number:03d} archived")
    return {"message": f"BL-{item.item_number:03d} archived"}


# ================================================================
# API: Item Activities
# ================================================================
@router.get("/items/{item_id}/activities", response_model=list[BacklogActivityRead])
async def get_item_activities(
    item_id: UUID,
    current_user: dict = Depends(require_backlog_access()),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the activity log for a backlog item, newest first."""
    item_result = await db.execute(
        select(BacklogItemModel).where(BacklogItemModel.id == item_id)
    )
    if not item_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Backlog item not found")

    result = await db.execute(
        select(BacklogActivityModel)
        .where(BacklogActivityModel.item_id == item_id)
        .order_by(BacklogActivityModel.created_at.desc())
    )
    return result.scalars().all()


# ================================================================
# HTML: Login + OAuth Callback
# ================================================================
@html_router.get("/backlog/login", response_class=HTMLResponse)
async def backlog_login(request: Request):
    """Backlog login page -- reuses testing login template."""
    return templates.TemplateResponse("backlog/login.html", {"request": request})


@html_router.get("/backlog/callback")
async def backlog_oauth_callback(request: Request, code: str = None, error: str = None):
    """OAuth2 callback -- exchanges code for token, redirects to board."""
    import httpx

    if error:
        logger.error(f"Backlog OAuth callback error: {error}")
        return RedirectResponse(url="/backlog/login?error=" + error)

    if not code:
        logger.warning("Backlog OAuth callback without code")
        return RedirectResponse(url="/backlog/login?error=no_code")

    keycloak_internal_url = "http://keycloak:8080"
    realm = "kc-camper-service-realm-dev"
    client_id = "camper_service_web"

    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "helix.local")
    redirect_uri = f"{forwarded_proto}://{forwarded_host}/backlog/callback"

    logger.info(f"Backlog token exchange redirect_uri: {redirect_uri}")

    token_endpoint = f"{keycloak_internal_url}/realms/{realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(f"Backlog token exchange failed: {response.status_code} - {response.text}")
                return RedirectResponse(url="/backlog/login?error=token_exchange_failed")

            tokens = response.json()
            access_token = tokens.get("access_token")

            if not access_token:
                logger.error("Backlog: No access_token in response")
                return RedirectResponse(url="/backlog/login?error=no_token")

            logger.info("Backlog OAuth callback successful, redirecting to board")
            return RedirectResponse(url=f"/backlog#token={access_token}")

    except Exception as e:
        logger.error(f"Backlog token exchange exception: {e}")
        return RedirectResponse(url="/backlog/login?error=token_exchange_error")


# ================================================================
# HTML: Board Page
# ================================================================
@html_router.get("/backlog", response_class=HTMLResponse)
async def backlog_board(request: Request):
    """Render the backlog board."""
    return templates.TemplateResponse("backlog/board.html", {"request": request})

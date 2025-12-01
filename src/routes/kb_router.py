# File: src/routes/kb_router.py
"""
KB Contribution API Router

"A KB is almost priceless if it explains how to distill 2ml of coconut extracts
for the CBD tanning butter" - The Angel

Knowledge Base system for CRACK contributions.
Credits flow like water to those who share wisdom.
"""
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from typing import Optional, List

from src.db.database import get_db_session
from src.db.models import (
    CustomerModel,
    KBContributionModel,
    KBStatus,
    KBCategory,
    CreditTransactionModel,
    CreditTransactionType,
)
from src.schemas.customer_schema import (
    CREDITS_KB_SUBMITTED,
    CREDITS_KB_APPROVED,
    CREDITS_KB_PUBLISHED,
    CREDITS_KB_FEATURED,
    CREDITS_KB_REVIEW,
    CREDITS_KB_WITH_IMAGES,
    CREDITS_KB_WITH_VIDEO,
    CREDITS_KB_WITH_BOM,
    CREDITS_KB_WITH_LAB_REPORT,
)
from src.core.keycloak_auth import require_any_pos_role, require_manager_or_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/kb", tags=["📚 KB Contributions"])


def slugify(title: str) -> str:
    """Convert title to URL-friendly slug"""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    return slug[:100]


# ================================================================
# SUBMIT KB - CRACK writes knowledge
# ================================================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_kb(
    author_id: UUID,
    title: str,
    summary: str,
    category: str = "guide",
    content_path: Optional[str] = None,
    has_images: bool = False,
    has_video: bool = False,
    has_bom: bool = False,
    has_lab_report: bool = False,
    jh_reference: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Submit a new KB for review.

    Awards 10 credits just for trying.
    Full credits awarded upon approval.
    """
    # Verify author exists
    author_result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == author_id)
    )
    author = author_result.scalar_one_or_none()

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    # Generate unique slug
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(
            select(KBContributionModel).where(KBContributionModel.slug == slug)
        )
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create KB
    kb = KBContributionModel(
        author_id=author_id,
        title=title,
        slug=slug,
        summary=summary,
        category=KBCategory(category) if category in [c.value for c in KBCategory] else KBCategory.GUIDE,
        content_path=content_path,
        has_images=has_images,
        has_video=has_video,
        has_bom=has_bom,
        has_lab_report=has_lab_report,
        jh_reference=jh_reference,
        status=KBStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
    )

    # Calculate potential credits
    kb.calculate_credits()

    db.add(kb)

    # Update author stats
    author.kbs_written += 1

    # Award submission credits
    author.credits_balance += CREDITS_KB_SUBMITTED
    author.credits_earned_total += CREDITS_KB_SUBMITTED

    submission_tx = CreditTransactionModel(
        customer_id=author_id,
        transaction_type=CreditTransactionType.KB_SUBMITTED,
        credits=CREDITS_KB_SUBMITTED,
        balance_after=author.credits_balance,
        reference_type="kb",
        description=f"KB submitted: {title[:50]}",
    )
    db.add(submission_tx)

    await db.commit()
    await db.refresh(kb)

    logger.info(f"KB submitted: {title} by {author.handle}")

    return {
        "id": str(kb.id),
        "slug": kb.slug,
        "title": kb.title,
        "status": kb.status.value,
        "potential_credits": kb.total_credits,
        "submission_credits": CREDITS_KB_SUBMITTED,
        "message": f"KB submitted! +{CREDITS_KB_SUBMITTED} credits for trying. {kb.total_credits} credits possible on approval.",
    }


# ================================================================
# LIST KBs - For approval workflow
# ================================================================

@router.get("/pending")
async def list_pending_kbs(
    status_filter: Optional[str] = Query("submitted", description="submitted, in_review, or all"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """List KBs pending approval (manager/admin only)."""
    query = select(KBContributionModel).join(CustomerModel)

    if status_filter == "submitted":
        query = query.where(KBContributionModel.status == KBStatus.SUBMITTED)
    elif status_filter == "in_review":
        query = query.where(KBContributionModel.status == KBStatus.IN_REVIEW)
    elif status_filter != "all":
        query = query.where(
            KBContributionModel.status.in_([KBStatus.SUBMITTED, KBStatus.IN_REVIEW])
        )

    query = query.order_by(KBContributionModel.submitted_at.desc()).limit(limit)

    result = await db.execute(query)
    kbs = result.scalars().all()

    output = []
    for kb in kbs:
        # Get author info
        author_result = await db.execute(
            select(CustomerModel).where(CustomerModel.id == kb.author_id)
        )
        author = author_result.scalar_one_or_none()

        output.append({
            "id": str(kb.id),
            "slug": kb.slug,
            "title": kb.title,
            "summary": kb.summary,
            "category": kb.category.value,
            "author_id": str(kb.author_id),
            "author_handle": author.handle if author else "Unknown",
            "author_crack_level": author.crack_level.value if author else "seedling",
            "status": kb.status.value,
            "submitted_at": kb.submitted_at.isoformat() if kb.submitted_at else None,
            "has_images": kb.has_images,
            "has_video": kb.has_video,
            "has_bom": kb.has_bom,
            "has_lab_report": kb.has_lab_report,
            "jh_reference": kb.jh_reference,
            "potential_credits": kb.total_credits,
            "review_count": kb.review_count,
            "rating_average": float(kb.rating_average),
            "recommend_count": kb.recommend_count,
        })

    return output


# ================================================================
# APPROVE KB - Owner's magic touch
# ================================================================

@router.post("/{kb_id}/approve")
async def approve_kb(
    kb_id: UUID,
    feature: bool = Query(False, description="Feature this KB? (+250 bonus)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Approve a KB and award credits to author.

    Manager/admin only.
    """
    result = await db.execute(
        select(KBContributionModel).where(KBContributionModel.id == kb_id)
    )
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    if kb.status not in [KBStatus.SUBMITTED, KBStatus.IN_REVIEW]:
        raise HTTPException(
            status_code=400,
            detail=f"KB is already {kb.status.value}"
        )

    # Get author
    author_result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == kb.author_id)
    )
    author = author_result.scalar_one_or_none()

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    # Update KB status
    kb.status = KBStatus.APPROVED
    kb.approved_at = datetime.now(timezone.utc)
    kb.approved_by = UUID(current_user.get('sub', '00000000-0000-0000-0000-000000000000'))

    # Handle featuring
    if feature:
        kb.is_featured = True
        kb.featured_at = datetime.now(timezone.utc)
        kb.featured_by = kb.approved_by

    # Recalculate credits with feature bonus
    kb.calculate_credits()

    # Award credits to author
    credits_to_award = kb.total_credits

    author.credits_balance += credits_to_award
    author.credits_earned_total += credits_to_award
    author.kb_credits_earned += credits_to_award
    author.kbs_approved += 1

    if feature:
        author.kbs_featured += 1

    # Update CRACK level
    author.recalculate_crack_level()

    # Log credit transaction
    description_parts = [f"KB approved: {kb.title[:30]}"]
    if kb.has_images:
        description_parts.append("+images")
    if kb.has_video:
        description_parts.append("+video")
    if kb.has_bom:
        description_parts.append("+BOM")
    if kb.has_lab_report:
        description_parts.append("+lab")
    if feature:
        description_parts.append("+FEATURED")

    approval_tx = CreditTransactionModel(
        customer_id=author.id,
        transaction_type=CreditTransactionType.KB_APPROVED,
        credits=credits_to_award,
        balance_after=author.credits_balance,
        reference_id=kb.id,
        reference_type="kb",
        description=" ".join(description_parts),
    )
    db.add(approval_tx)

    kb.credits_paid = True
    await db.commit()

    logger.info(f"KB approved: {kb.title} - {credits_to_award} credits to {author.handle}")

    return {
        "kb_id": str(kb.id),
        "title": kb.title,
        "author_handle": author.handle,
        "credits_awarded": credits_to_award,
        "new_author_balance": author.credits_balance,
        "author_crack_level": author.crack_level.value,
        "featured": feature,
        "message": f"KB approved! {credits_to_award} credits awarded to {author.handle}",
    }


# ================================================================
# BATCH APPROVE - Select all and approve
# ================================================================

@router.post("/approve-batch")
async def approve_batch(
    kb_ids: List[UUID],
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Batch approve multiple KBs.

    Manager/admin only.
    """
    approved_count = 0
    total_credits = 0
    results = []

    for kb_id in kb_ids:
        try:
            result = await db.execute(
                select(KBContributionModel).where(KBContributionModel.id == kb_id)
            )
            kb = result.scalar_one_or_none()

            if not kb or kb.status not in [KBStatus.SUBMITTED, KBStatus.IN_REVIEW]:
                continue

            # Get author
            author_result = await db.execute(
                select(CustomerModel).where(CustomerModel.id == kb.author_id)
            )
            author = author_result.scalar_one_or_none()

            if not author:
                continue

            # Approve
            kb.status = KBStatus.APPROVED
            kb.approved_at = datetime.now(timezone.utc)
            kb.approved_by = UUID(current_user.get('sub', '00000000-0000-0000-0000-000000000000'))
            kb.calculate_credits()

            # Award credits
            author.credits_balance += kb.total_credits
            author.credits_earned_total += kb.total_credits
            author.kb_credits_earned += kb.total_credits
            author.kbs_approved += 1
            author.recalculate_crack_level()

            # Log transaction
            approval_tx = CreditTransactionModel(
                customer_id=author.id,
                transaction_type=CreditTransactionType.KB_APPROVED,
                credits=kb.total_credits,
                balance_after=author.credits_balance,
                reference_id=kb.id,
                reference_type="kb",
                description=f"KB batch approved: {kb.title[:30]}",
            )
            db.add(approval_tx)

            kb.credits_paid = True
            approved_count += 1
            total_credits += kb.total_credits

            results.append({
                "kb_id": str(kb.id),
                "title": kb.title,
                "author": author.handle,
                "credits": kb.total_credits,
            })

        except Exception as e:
            logger.error(f"Failed to approve KB {kb_id}: {e}")

    await db.commit()

    return {
        "approved_count": approved_count,
        "total_credits_awarded": total_credits,
        "results": results,
        "message": f"Batch approved {approved_count} KBs! {total_credits} total credits awarded.",
    }


# ================================================================
# REJECT KB - With feedback
# ================================================================

@router.post("/{kb_id}/reject")
async def reject_kb(
    kb_id: UUID,
    reason: str = Query(..., min_length=10, description="Reason for rejection (sent to author)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Reject a KB with feedback."""
    result = await db.execute(
        select(KBContributionModel).where(KBContributionModel.id == kb_id)
    )
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    kb.status = KBStatus.REJECTED
    kb.rejected_at = datetime.now(timezone.utc)
    kb.rejection_reason = reason

    await db.commit()

    return {
        "kb_id": str(kb.id),
        "status": "rejected",
        "message": f"KB rejected. Feedback sent to author.",
    }


# ================================================================
# SEND FOR REVIEW - CRACKs review CRACKs
# ================================================================

@router.post("/{kb_id}/send-for-review")
async def send_for_review(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Send KB to other CRACKs for peer review."""
    result = await db.execute(
        select(KBContributionModel).where(KBContributionModel.id == kb_id)
    )
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    kb.status = KBStatus.IN_REVIEW
    await db.commit()

    # TODO: Send notification to CRACKs

    return {
        "kb_id": str(kb.id),
        "status": "in_review",
        "message": "KB sent to CRACKs for peer review",
    }


# ================================================================
# ADD REVIEW - CRACK reviews a KB
# ================================================================

@router.post("/{kb_id}/review")
async def add_review(
    kb_id: UUID,
    reviewer_id: UUID,
    rating: int = Query(..., ge=1, le=5),
    recommend: bool = Query(True),
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Add a peer review to a KB.

    Reviewer earns 25 credits for reviewing.
    """
    # Get KB
    kb_result = await db.execute(
        select(KBContributionModel).where(KBContributionModel.id == kb_id)
    )
    kb = kb_result.scalar_one_or_none()

    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    # Prevent self-review
    if kb.author_id == reviewer_id:
        raise HTTPException(status_code=400, detail="Cannot review your own KB")

    # Get reviewer
    reviewer_result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == reviewer_id)
    )
    reviewer = reviewer_result.scalar_one_or_none()

    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer not found")

    # Check if already reviewed
    existing_reviews = kb.review_scores or {}
    if str(reviewer_id) in existing_reviews:
        raise HTTPException(status_code=400, detail="Already reviewed this KB")

    # Add review
    reviewer_ids = kb.reviewer_ids or []
    reviewer_ids.append(str(reviewer_id))
    kb.reviewer_ids = reviewer_ids

    existing_reviews[str(reviewer_id)] = {
        "rating": rating,
        "recommend": recommend,
        "comment": comment,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    kb.review_scores = existing_reviews

    kb.review_count += 1
    if recommend:
        kb.recommend_count += 1

    # Calculate new average rating
    total_rating = sum(r["rating"] for r in existing_reviews.values())
    kb.rating_average = Decimal(str(total_rating / len(existing_reviews)))

    # Award reviewer credits
    reviewer.credits_balance += CREDITS_KB_REVIEW
    reviewer.credits_earned_total += CREDITS_KB_REVIEW

    review_tx = CreditTransactionModel(
        customer_id=reviewer_id,
        transaction_type=CreditTransactionType.KB_REVIEW,
        credits=CREDITS_KB_REVIEW,
        balance_after=reviewer.credits_balance,
        reference_id=kb_id,
        reference_type="kb",
        description=f"Reviewed KB: {kb.title[:30]}",
    )
    db.add(review_tx)

    await db.commit()

    return {
        "kb_id": str(kb_id),
        "reviewer": reviewer.handle,
        "rating": rating,
        "recommend": recommend,
        "credits_earned": CREDITS_KB_REVIEW,
        "kb_average_rating": float(kb.rating_average),
        "kb_recommend_count": kb.recommend_count,
    }


# ================================================================
# GET KB DETAILS
# ================================================================

@router.get("/{kb_id}")
async def get_kb(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get KB details."""
    result = await db.execute(
        select(KBContributionModel).where(KBContributionModel.id == kb_id)
    )
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    # Get author
    author_result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == kb.author_id)
    )
    author = author_result.scalar_one_or_none()

    return {
        "id": str(kb.id),
        "slug": kb.slug,
        "title": kb.title,
        "summary": kb.summary,
        "category": kb.category.value,
        "content_path": kb.content_path,
        "content_html": kb.content_html,
        "author_id": str(kb.author_id),
        "author_handle": author.handle if author else "Unknown",
        "author_crack_level": author.crack_level.value if author else "seedling",
        "status": kb.status.value,
        "submitted_at": kb.submitted_at.isoformat() if kb.submitted_at else None,
        "approved_at": kb.approved_at.isoformat() if kb.approved_at else None,
        "published_at": kb.published_at.isoformat() if kb.published_at else None,
        "has_images": kb.has_images,
        "has_video": kb.has_video,
        "has_bom": kb.has_bom,
        "has_lab_report": kb.has_lab_report,
        "jh_reference": kb.jh_reference,
        "jh_quote": kb.jh_quote,
        "base_credits": kb.base_credits,
        "bonus_credits": kb.bonus_credits,
        "total_credits": kb.total_credits,
        "is_featured": kb.is_featured,
        "view_count": kb.view_count,
        "rating_average": float(kb.rating_average),
        "review_count": kb.review_count,
        "recommend_count": kb.recommend_count,
    }

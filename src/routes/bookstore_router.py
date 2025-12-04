# File: src/routes/bookstore_router.py
"""
HelixBOOKSTORE API Router
"Be water, my friend." - Bruce Lee
"Start with books." - Jeff Bezos (but Bruce does it better)

1291: One page for Switzerland
2025: One router for books
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID

from src.db.database import get_db
from src.db.models.book_model import BookModel, BookGenre, BookFormat
from src.schemas.book_schema import (
    BookCreate, BookUpdate, BookRead, BookSearch, BookstoreStats,
    BookGenreEnum
)

router = APIRouter(prefix="/api/v1/books", tags=["Bookstore"])


# ================================================================
# CRUD OPERATIONS - Simple like Tell's crossbow
# ================================================================

@router.post("/", response_model=BookRead, status_code=201)
async def create_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a book to the store.
    Like adding an arrow to the quiver.
    """
    db_book = BookModel(
        isbn=book.isbn,
        isbn_13=book.isbn_13,
        title=book.title,
        subtitle=book.subtitle,
        author=book.author,
        publisher=book.publisher,
        publication_year=book.publication_year,
        genre=BookGenre[book.genre.name] if book.genre else BookGenre.OTHER,
        subjects=book.subjects,
        format=BookFormat[book.format.name] if book.format else BookFormat.PAPERBACK,
        pages=book.pages,
        language=book.language,
        description=book.description,
        cover_image_url=book.cover_image_url,
        is_miracle_book=book.is_miracle_book,
        angel_notes=book.angel_notes,
        product_id=book.product_id
    )
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book


@router.get("/", response_model=list[BookRead])
async def list_books(
    genre: Optional[BookGenreEnum] = None,
    author: Optional[str] = None,
    miracle_only: bool = False,
    search: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List books. Filter by genre, author, or search.
    The 98% deserve a simple catalog.
    """
    query = select(BookModel)

    if genre:
        query = query.where(BookModel.genre == BookGenre[genre.name])
    if author:
        query = query.where(BookModel.author.ilike(f"%{author}%"))
    if miracle_only:
        query = query.where(BookModel.is_miracle_book == True)
    if search:
        query = query.where(
            (BookModel.title.ilike(f"%{search}%")) |
            (BookModel.author.ilike(f"%{search}%")) |
            (BookModel.isbn.ilike(f"%{search}%"))
        )

    query = query.order_by(BookModel.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/miracle-books", response_model=list[BookRead])
async def list_miracle_books(
    db: AsyncSession = Depends(get_db)
):
    """
    The books that changed lives.
    Maria's 4 AM companions. Angel's grade 9 report.
    """
    query = select(BookModel).where(
        BookModel.is_miracle_book == True
    ).order_by(BookModel.title)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/isbn/{isbn}", response_model=BookRead)
async def get_book_by_isbn(
    isbn: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Find a book by ISBN - the book's barcode.
    The second arrow finds its target.
    """
    query = select(BookModel).where(
        (BookModel.isbn == isbn) | (BookModel.isbn_13 == isbn)
    )
    result = await db.execute(query)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/{book_id}", response_model=BookRead)
async def get_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a book by ID"""
    query = select(BookModel).where(BookModel.id == book_id)
    result = await db.execute(query)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: UUID,
    book_update: BookUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a book"""
    query = select(BookModel).where(BookModel.id == book_id)
    result = await db.execute(query)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = book_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'genre' and value:
            value = BookGenre[value.name]
        if field == 'format' and value:
            value = BookFormat[value.name]
        setattr(book, field, value)

    await db.commit()
    await db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a book"""
    query = select(BookModel).where(BookModel.id == book_id)
    result = await db.execute(query)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    await db.delete(book)
    await db.commit()


# ================================================================
# STATS - For Felix and Angel
# ================================================================

@router.get("/stats/overview", response_model=BookstoreStats)
async def get_bookstore_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Bookstore statistics.
    What Albert would want to see at 6 AM.
    """
    # Total books
    total_result = await db.execute(select(func.count(BookModel.id)))
    total_books = total_result.scalar() or 0

    # Miracle books
    miracle_result = await db.execute(
        select(func.count(BookModel.id)).where(BookModel.is_miracle_book == True)
    )
    total_miracle = miracle_result.scalar() or 0

    # By genre
    genre_result = await db.execute(
        select(BookModel.genre, func.count(BookModel.id))
        .group_by(BookModel.genre)
    )
    books_by_genre = {str(row[0].value): row[1] for row in genre_result.all()}

    # Top authors
    author_result = await db.execute(
        select(BookModel.author, func.count(BookModel.id))
        .group_by(BookModel.author)
        .order_by(func.count(BookModel.id).desc())
        .limit(10)
    )
    top_authors = [{"author": row[0], "count": row[1]} for row in author_result.all()]

    # Recent additions
    recent_result = await db.execute(
        select(BookModel)
        .order_by(BookModel.created_at.desc())
        .limit(5)
    )
    recent_books = recent_result.scalars().all()

    return BookstoreStats(
        total_books=total_books,
        total_miracle_books=total_miracle,
        books_by_genre=books_by_genre,
        top_authors=top_authors,
        recent_additions=recent_books
    )

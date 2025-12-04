# File: src/schemas/book_schema.py
"""
Pydantic schemas for HelixBOOKSTORE.
Jeff started with books. Bruce does it with water.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum


class BookFormatEnum(str, Enum):
    """Book format types"""
    HARDCOVER = "hardcover"
    PAPERBACK = "paperback"
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"


class BookGenreEnum(str, Enum):
    """Book genres"""
    RELIGIOUS = "religious"
    SPIRITUAL = "spiritual"
    FICTION = "fiction"
    NON_FICTION = "non_fiction"
    BIOGRAPHY = "biography"
    HISTORY = "history"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    SELF_HELP = "self_help"
    CHILDREN = "children"
    CLASSIC = "classic"
    OTHER = "other"


# ================================================================
# BOOK SCHEMAS
# ================================================================

class BookBase(BaseModel):
    """Base book fields"""
    isbn: Optional[str] = Field(None, max_length=20, description="ISBN-10 or ISBN-13")
    isbn_13: Optional[str] = Field(None, max_length=13, description="ISBN-13")
    title: str = Field(..., max_length=500, description="Book title")
    subtitle: Optional[str] = Field(None, max_length=500, description="Subtitle")
    author: str = Field(..., max_length=255, description="Author name(s)")
    publisher: Optional[str] = Field(None, max_length=255, description="Publisher")
    publication_year: Optional[int] = Field(None, ge=1000, le=2100, description="Publication year")
    genre: BookGenreEnum = Field(default=BookGenreEnum.OTHER, description="Primary genre")
    subjects: Optional[str] = Field(None, description="Comma-separated subjects")
    format: BookFormatEnum = Field(default=BookFormatEnum.PAPERBACK, description="Book format")
    pages: Optional[int] = Field(None, ge=1, description="Page count")
    language: str = Field(default="English", max_length=50, description="Language")
    description: Optional[str] = Field(None, description="Book description")
    cover_image_url: Optional[str] = Field(None, max_length=500, description="Cover image URL")
    is_miracle_book: bool = Field(default=False, description="Books that changed lives")
    angel_notes: Optional[str] = Field(None, description="Personal notes - why this book matters")


class BookCreate(BookBase):
    """Schema for creating a new book"""
    product_id: Optional[UUID] = Field(None, description="Link to product for POS")


class BookUpdate(BaseModel):
    """Schema for updating a book (all fields optional)"""
    isbn: Optional[str] = Field(None, max_length=20)
    isbn_13: Optional[str] = Field(None, max_length=13)
    title: Optional[str] = Field(None, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=255)
    publisher: Optional[str] = Field(None, max_length=255)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    genre: Optional[BookGenreEnum] = None
    subjects: Optional[str] = None
    format: Optional[BookFormatEnum] = None
    pages: Optional[int] = Field(None, ge=1)
    language: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    cover_image_url: Optional[str] = Field(None, max_length=500)
    is_miracle_book: Optional[bool] = None
    angel_notes: Optional[str] = None
    product_id: Optional[UUID] = None


class BookRead(BookBase):
    """Schema for reading a book"""
    id: UUID
    product_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookSearch(BaseModel):
    """Schema for searching books"""
    query: Optional[str] = Field(None, description="Search title, author, ISBN")
    genre: Optional[BookGenreEnum] = None
    author: Optional[str] = None
    is_miracle_book: Optional[bool] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ================================================================
# BOOKSTORE STATS
# ================================================================

class BookstoreStats(BaseModel):
    """Bookstore statistics - for Felix and Angel"""
    total_books: int
    total_miracle_books: int
    books_by_genre: dict[str, int]
    top_authors: list[dict]
    recent_additions: list[BookRead]

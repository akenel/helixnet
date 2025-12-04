# File: src/db/models/book_model.py
"""
BookModel - Bruce Lee Bookstore Extension
"Be water, my friend." - Start with books, like Jeff did.

This extends ProductModel for book-specific fields.
ISBN is the barcode. Author is the supplier. Simple.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class BookFormat(enum.Enum):
    """Book format types"""
    HARDCOVER = "hardcover"
    PAPERBACK = "paperback"
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"


class BookGenre(enum.Enum):
    """Book genres - keep it simple like Tell's one page"""
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


class BookModel(Base):
    """
    Book catalog for HelixBOOKSTORE.

    Jeff started with books. Bruce does it better.
    One page was enough for Switzerland. One model is enough for books.
    """
    __tablename__ = 'books'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Link to Product (optional - can be standalone or linked)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('products.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Link to ProductModel for POS integration"
    )

    # Book Identity - The Second Arrow
    isbn: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=True,
        comment="ISBN-10 or ISBN-13 - the book's barcode"
    )
    isbn_13: Mapped[str | None] = mapped_column(
        String(13),
        unique=True,
        index=True,
        nullable=True,
        comment="ISBN-13 format"
    )

    # Book Details
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Book title"
    )
    subtitle: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Book subtitle"
    )
    author: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Author name(s) - comma separated for multiple"
    )
    publisher: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Publisher name"
    )
    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Year of publication"
    )

    # Classification
    genre: Mapped[BookGenre] = mapped_column(
        SQLEnum(BookGenre),
        default=BookGenre.OTHER,
        nullable=False,
        comment="Primary genre"
    )
    subjects: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated subject tags"
    )

    # Physical Details
    format: Mapped[BookFormat] = mapped_column(
        SQLEnum(BookFormat),
        default=BookFormat.PAPERBACK,
        nullable=False,
        comment="Book format"
    )
    pages: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Page count"
    )
    language: Mapped[str] = mapped_column(
        String(50),
        default="English",
        nullable=False,
        comment="Book language"
    )

    # Content
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Book description/summary"
    )
    cover_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Cover image URL"
    )

    # Angel's Special Field - The Miracle Books
    is_miracle_book: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Books that changed lives - like 'This is Ann Speaking'"
    )
    angel_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Personal notes - why this book matters"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<BookModel(isbn='{self.isbn}', title='{self.title}', author='{self.author}')>"


# ================================================================
# SAMPLE BOOKS - The First 10 Like Jeff Did
# ================================================================
SAMPLE_BOOKS = [
    {
        "title": "This Is Ann Speaking",
        "author": "Ann",
        "genre": BookGenre.RELIGIOUS,
        "format": BookFormat.PAPERBACK,
        "description": "A little girl talks to the Lord. Simple. Sweet. True.",
        "is_miracle_book": True,
        "angel_notes": "Grade 9 book report. Mr. Shima. Changed everything."
    },
    {
        "title": "The Bible",
        "author": "Various",
        "genre": BookGenre.RELIGIOUS,
        "format": BookFormat.HARDCOVER,
        "description": "The Word. Maria's 4 AM companion.",
        "is_miracle_book": True,
        "angel_notes": "Maria started at 4 AM. Every day."
    },
    {
        "title": "Water Fuel Cell Technical Brief",
        "author": "Stanley Meyer",
        "genre": BookGenre.TECHNOLOGY,
        "format": BookFormat.PAPERBACK,
        "description": "Stan the Man. The water fuel cell.",
        "is_miracle_book": True,
        "angel_notes": "The SACHS Wankels. Oliver thought I was a nut."
    },
]

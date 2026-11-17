from typing import Optional

from sqlalchemy import CheckConstraint, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1888 AND 2100", name="ck_movies_year"),
        CheckConstraint("section IN ('mainstream', 'hidden_gem')", name="ck_movies_section"),
        CheckConstraint("rating BETWEEN 0 AND 10", name="ck_movies_rating"),
        CheckConstraint("reviews_count >= 0", name="ck_movies_reviews_count"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(1000), default="", server_default="")
    poster_url: Mapped[Optional[str]] = mapped_column(Text)
    trailer_url: Mapped[Optional[str]] = mapped_column(Text)
    section: Mapped[str] = mapped_column(String(20), default="mainstream", server_default="mainstream")
    rating: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan", passive_deletes=True)
    watchlist_items = relationship("WatchlistItem", back_populates="movie", cascade="all, delete-orphan", passive_deletes=True)


Index("uq_movies_title_lower_year", func.lower(Movie.title), Movie.year, unique=True)

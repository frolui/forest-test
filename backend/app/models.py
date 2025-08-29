from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB, CITEXT
from geoalchemy2.types import Geometry


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    map_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.id} {self.username!r}>"


class Layer(Base):
    __tablename__ = "layers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    # bbox geometry(Polygon, 4326)
    bbox: Mapped[Optional[object]] = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)

    features: Mapped[list["Feature"]] = relationship(
        back_populates="layer",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<Layer {self.id} {self.name!r}>"


class Feature(Base):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(primary_key=True)
    layer_id: Mapped[int] = mapped_column(ForeignKey("layers.id", ondelete="CASCADE"), index=True)
    properties: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    # geom geometry(Geometry, 4326)
    geom: Mapped[object] = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    layer: Mapped["Layer"] = relationship(back_populates="features")

    def __repr__(self) -> str:
        return f"<Feature {self.id} layer={self.layer_id}>"

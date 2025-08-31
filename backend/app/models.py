from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, text, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, CITEXT
from geoalchemy2.types import Geometry


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(CITEXT, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    map_state: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    layers: Mapped[list["Layer"]] = relationship(
        back_populates="owner",
        passive_deletes=True,
        lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<User {self.id} {self.username!r}>"


class Layer(Base):
    __tablename__ = "layers"
    __table_args__ = (
        UniqueConstraint("public_id", "owner_id", name="idx_layers_public_id_owner_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(50), server_default=text("gen_random_uuid()"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    copyrights: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    bbox: Mapped[Optional[object]] = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)

    owner: Mapped["User"] = relationship(
        back_populates="layers",
        lazy="raise"
    )
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
    __table_args__ = (
        UniqueConstraint("layer_id", "source_id", name="uq_features_layer_id_source_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    layer_id: Mapped[int] = mapped_column(ForeignKey("layers.id", ondelete="CASCADE"), index=True, nullable=False)
    properties: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    geom: Mapped[object] = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    geom_3857: Mapped[Optional[object]] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=3857),
        nullable=True
    )

    layer: Mapped["Layer"] = relationship(back_populates="features")

    def __repr__(self) -> str:
        return f"<Feature {self.id} layer={self.layer_id}>"

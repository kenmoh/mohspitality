from random import random
from typing import Any
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Dialect
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import CHAR
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import TypeDecorator

from app.schemas.user_schema import PaymentGatwayEnum, SubscriptionType, UserType


class OrderNumber(TypeDecorator):
    impl = CHAR

    def __init__(self, length=10, *args, **kwargs):
        super(OrderNumber, self).__init__(length, *args, **kwargs)

    def process_bind_param(self, value: str, dialect: Dialect) -> Any:
        if value is None:
            return generate_order_number()
        return value

    def process_result_value(self, value: str, dialect: Dialect) -> str:
        return value


def user_unique_id():
    return str(uuid.uuid1()).replace("-", "")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, default=user_unique_id, index=True
    )
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    user_type: Mapped[UserType] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_subscribed: Mapped[bool] = mapped_column(default=False)
    notification_token: Mapped[str] = mapped_column(nullable=True)
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        nullable=True, default=SubscriptionType.TRIAL)
    is_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Company who created this staff (if applicable)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Relationships
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    password_resets = relationship(
        "PasswordReset", back_populates="user", cascade="all, delete-orphan"
    )
    user_profile = relationship(
        "UserProfile", back_populates="user", uselist=False)
    company_profile = relationship(
        "CompanyProfile", back_populates="user", uselist=False
    )
    company = relationship("User", back_populates="staff", remote_side=[id])
    staff = relationship("User", back_populates="company")
    payment_gateway = relationship(
        "PaymentGateway", back_populates="user", uselist=False
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, default=user_unique_id, index=True
    )
    full_name: Mapped[str] = mapped_column(nullable=True)
    phone_number: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", back_populates="user_profile")


class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    id: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, default=user_unique_id, index=True
    )

    company_name: Mapped[str] = mapped_column()
    address: Mapped[str] = mapped_column()
    phone_number: Mapped[str] = mapped_column(nullable=True)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    logo_url: Mapped[str] = mapped_column(nullable=True)
    user = relationship("User", back_populates="company_profile")


class PaymentGateway(Base):
    __tablename__ = "payment_gateways"
    id: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, default=user_unique_id, index=True
    )
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    api_key: Mapped[str] = mapped_column()
    api_secret: Mapped[str] = mapped_column()
    payment_gateway: Mapped[PaymentGatwayEnum] = mapped_column()
    user = relationship("User", back_populates="payment_gateway")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, default=user_unique_id, index=True
    )
    token: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_revoked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", back_populates="refresh_tokens")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, default=user_unique_id, index=True
    )
    token: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", back_populates="password_resets")


class Association(Base):
    __tablename__ = "association_table"
    left_id: Mapped[int] = mapped_column(
        ForeignKey("left_table.id"), primary_key=True)
    right_id: Mapped[int] = mapped_column(
        ForeignKey("right_table.id"), primary_key=True
    )
    child: Mapped["Child"] = relationship(back_populates="parents")
    parent: Mapped["Parent"] = relationship(back_populates="children")

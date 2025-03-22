from decimal import Decimal
from random import random
from typing import Any
import uuid
from datetime import datetime
from sqlalchemy import JSON, DateTime, Dialect
from sqlalchemy.sql import func
from app.database.db import Base
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import CHAR, JSONB
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import TypeDecorator

from app.schemas.room_schema import OutletType
from app.schemas.subscriptions import SubscriptionStatus, SubscriptionType
from app.schemas.user_schema import CurencySymbol, PaymentGatwayEnum, UserType


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
        nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    role_id: Mapped[int] = mapped_column(ForeignKey(
        "roles.id", ondelete="SET NULL"), nullable=True)
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
    subscriptions = relationship("Subscription", back_populates="user")
    # role = relationship("Role", back_populates="user")
    role = relationship("Role", back_populates="users", foreign_keys=[role_id])
    company_roles = relationship(
        "Role", back_populates="company", primaryjoin="User.id==Role.company_id")

    qrcodes = relationship("QRCode", back_populates="user")
    departments = relationship("Department", back_populates="user")
    outlets = relationship("Outlet", back_populates="user")
    no_post_list = relationship("NoPost", back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(primary_key=True, nullable=False,
                                    default=user_unique_id, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    plan_name: Mapped[SubscriptionType] = mapped_column(
        default=SubscriptionType.TRIAL)
    amount: Mapped[Decimal] = mapped_column(default=0.00)
    # e.g., active, canceled
    status: Mapped[SubscriptionStatus] = mapped_column(
        default=SubscriptionStatus.ACTIVE)
    payment_link: Mapped[str] = mapped_column(nullable=True)
    # You might want to use Date or DateTime
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    # You might want to use Date or DateTime
    end_date: Mapped[datetime] = mapped_column()

    user = relationship("User", back_populates="subscriptions")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, default=user_unique_id, index=True
    )
    full_name: Mapped[str] = mapped_column()
    phone_number: Mapped[str] = mapped_column(unique=True)
    department: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", back_populates="user_profile")


class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    id: Mapped[str] = mapped_column(
        primary_key=True, nullable=False, default=user_unique_id, index=True
    )

    company_name: Mapped[str] = mapped_column(unique=True)
    address: Mapped[str] = mapped_column()
    phone_number: Mapped[str] = mapped_column(unique=True)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    logo_url: Mapped[str] = mapped_column(nullable=True)
    currency_symbol: Mapped[CurencySymbol] = mapped_column(
        nullable=True, default=CurencySymbol.NGN)
    user = relationship("User", back_populates="company_profile")

    api_key: Mapped[str] = mapped_column(unique=True)
    api_secret: Mapped[str] = mapped_column(unique=True)
    payment_gateway: Mapped[PaymentGatwayEnum] = mapped_column()


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True, autoincrement=True
    )

    name: Mapped[str] = mapped_column(unique=False)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user_permissions: Mapped[list[str]
                             ] = mapped_column(JSON, default=list)
    company = relationship(
        "User", back_populates="company_roles", foreign_keys=[company_id])
    users = relationship("User", back_populates="role",
                         foreign_keys=[User.role_id])

    __table_args__ = (
        UniqueConstraint("name", "company_id", name="role_name"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True, autoincrement=True
    )

    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column()


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True, autoincrement=True
    )
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(unique=False)
    user = relationship("User", back_populates="departments")
    __table_args__ = (
        UniqueConstraint("name", "company_id", name="department_name"),
    )


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True, autoincrement=True
    )
    company_id: Mapped[str]

    message: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class NoPost(Base):
    __tablename__ = "no_post_list"
    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True, autoincrement=True
    )
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    no_post_list: Mapped[str]
    user = relationship("User", back_populates="no_post_list")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class Outlet(Base):
    __tablename__ = "outlets"
    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True
    )
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str]
    user = relationship("User", back_populates="outlets")

    __table_args__ = (
        UniqueConstraint("name", "company_id", name="outlet_name"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QRCode(Base):
    __tablename__ = "qrcodes"
    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True
    )
    company_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    room_or_table_numbers: Mapped[str]
    fill_color: Mapped[str] = mapped_column(nullable=True)
    back_color: Mapped[str] = mapped_column(nullable=True)
    outlet_type: Mapped[OutletType]
    user = relationship("User", back_populates="qrcodes")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


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


class QRCodeLimit(Base):
    __tablename__ = "qrcode_limits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        default=SubscriptionType.TRIAL)
    max_qrcodes: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())

# class Association(Base):
#     __tablename__ = "association_table"
#     left_id: Mapped[int] = mapped_column(
#         ForeignKey("left_table.id"), primary_key=True)
#     right_id: Mapped[int] = mapped_column(
#         ForeignKey("right_table.id"), primary_key=True
#     )
#     child: Mapped["Child"] = relationship(back_populates="parents")
#     parent: Mapped["Parent"] = relationship(back_populates="children")

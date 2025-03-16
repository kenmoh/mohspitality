from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, Tuple
from datetime import datetime, timedelta
import uuid
from jose import jwt
from passlib.context import CryptContext

from app.auth.models import User, PasswordReset
from app.auth.schemas import UserCreate, UserLogin, UserUpdate, UserUpdatePassword
from app.config import settings
from app.models.user_models import RefreshToken
from app.schemas.user_schema import MessageSchema, PasswordResetConfirm, PasswordResetRequest, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def create_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
    """
    Create a new user in the database.

    Args:
        db: Database session
        user_data: User data from request
        created_by_id: ID of the user who is creating this user (optional)

    Returns:
        The newly created user
    """
    # Check if email already exists
    email_exists = await db.execute(select(User).where(User.email == user_data.email))
    if email_exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create the user
    user = User(
        email=user_data.email,
        password=hash_password(user_data.password),  # Hash password
        is_active=True,
        is_superuser=False,
    )

    # Add user to database
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(**user)


async def login_user(db: AsyncSession, login_data: UserLogin) -> User:
    """   
    Args:
            db: Database session
            login_data: Login credentials

    Returns:
            Authenticated user or None if authentication fails
    """
    # Find user by username
    stmt = select(User).where(User.username == login_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    # Verify password
    if not verify_password(login_data.password, user.password):
        return None

    # Check if user is active
    if not user.is_active:
        return None

    return user


async def update_user(db: AsyncSession, user_id: str, user_data: UserLogin) -> User:
    """	
    Args:
            db: Database session
            user_id: ID of the user to update
            user_data: Updated user data

    Returns:
            Updated user
    """
    # Get the user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update values that are provided
    if user_data.email is not None:
        # Check if email is already taken by another user
        stmt = select(User).where(
            User.email == user_data.email, User.id != user_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        user.email = user_data.email

    # Save changes
    await db.commit()
    await db.refresh(user)

    return user


async def update_password(db: AsyncSession, user_id: str, password_data: UserUpdatePassword) -> User:
    """
    Args:
            db: Database session
            user_id: ID of the user to update
            password_data: Current and new password

    Returns:
            Updated user
    """
    # Get the user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash and set new password
    user.password = hash_password(password_data.new_password)

    # Revoke all refresh tokens for this user
    await db.execute((RefreshToken)
                     .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
                     .values(is_revoked=True)
                     )

    # Save changes
    await db.commit()
    await db.refresh(user)

    return user


async def send_password_reset_email(email: str, reset_token: str, background_tasks: BackgroundTasks):
    """
    Send a password reset email to the user.
    Args:
            email: Email address of the user
            reset_token: Password reset token
            background_tasks: FastAPI background tasks
    """
    # Create reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    # Create email message
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"""
		<html>
		<body>
		    <p>We received a request to reset your password. If you didn't make this request, please ignore this email.</p>
		    <p>To reset your password, click the link below:</p>
		    <p><a href="{reset_link}">Reset Password</a></p>
		    <p>This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours.</p>
		</body>
		</html>
		""",
        subtype="html"
    )

    # Send email in background
    fastmail = FastMail(mail_config)
    background_tasks.add_task(fastmail.send_message, message)


async def request_password_reset(db: AsyncSession, reset_request: PasswordResetRequest, background_tasks: BackgroundTasks) -> bool:
    """
    Request a password reset for a user.
    Args:
            db: Database session
            reset_request: Password reset request data
            background_tasks: FastAPI background tasks

    Returns:
            True if password reset was requested successfully
    """
    # Find user by email
    stmt = select(User).where(User.email == reset_request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Always return true, even if user not found, to prevent email enumeration
    if not user:
        return True

    # Generate reset token
    reset_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

    # Create password reset record
    password_reset = PasswordReset(
        token=reset_token,
        user_id=user.id,
        expires_at=expires_at
    )

    # Add password reset to database
    db.add(password_reset)
    await db.commit()

    # Send password reset email
    await send_password_reset_email(user.email, reset_token, background_tasks)

    return True


async def confirm_password_reset(db: AsyncSession, reset_confirm: PasswordResetConfirm) -> User:
    """
    Confirm a password reset and change the user's password.
    Args:
            db: Database session
            reset_confirm: Password reset confirmation data

    Returns:
            User with updated password
    """
    # Find password reset record
    stmt = select(PasswordReset).where(
        PasswordReset.token == reset_confirm.token,
        PasswordReset.expires_at > datetime.utcnow(),
        PasswordReset.is_used == False
    )
    result = await db.execute(stmt)
    password_reset = result.scalar_one_or_none()

    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )

    # Get the user
    stmt = select(User).where(User.id == password_reset.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Mark token as used
    password_reset.is_used = True

    # Hash and set new password
    user.hashed_password = hash_password(reset_confirm.new_password)

    # Revoke all refresh tokens for this user
    await db.execute(
        update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.is_revoked == False)
            .values(is_revoked=True)
    )

    # Save changes
    await db.commit()

    return user

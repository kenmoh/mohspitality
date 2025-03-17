from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_models import UserProfile, CompanyProfile, User

from app.schemas.profile_schema import (
    CreateCompanyProfile,
    CreateStaffUserProfile,
    CreateUserProfileBase,
    CreateCompanyProfileResponse,
    UpdateCompanyPaymentGateway,
    UpdateCompanyProfile,
)


async def create_company_profile(
    db: AsyncSession, data: CreateCompanyProfile, current_user: User
) -> CreateCompanyProfileResponse:
    try:
        # Create Profile
        company_profile = CompanyProfile(
            company_name=data.company_name,
            phone_number=data.phone_number,
            address=data.address,
            api_key=data.api_key,
            api_secret=data.api_secret,
            payment_gateway=data.payment_gateway,
            company_id=current_user.id,
        )

        # Add profile to database
        db.add(company_profile)
        await db.commit()
        await db.refresh(company_profile)

        return CreateCompanyProfileResponse(**company_profile)
    except Exception as e:
        raise e


async def create_guest_profile(
    db: AsyncSession, data: CreateUserProfileBase, current_user: User
) -> CreateUserProfileBase:
    try:
        # Create Profile
        guest_profile = UserProfile(
            full_name=data.company_name,
            phone_number=data.phone_number,
            user_id=current_user.id,
        )

        # Add profile to database
        db.add(guest_profile)
        await db.commit()
        await db.refresh(guest_profile)

        return CreateUserProfileBase(**guest_profile)
    except Exception as e:
        raise e


async def create_staff_profile(
    db: AsyncSession, data: CreateStaffUserProfile, current_user: User
) -> CreateStaffUserProfile:
    try:
        # Create Profile
        staff_profile = UserProfile(
            full_name=data.company_name,
            phone_number=data.phone_number,
            department=data.department,
            user_id=current_user.id,
        )

        # Add user to database
        db.add(staff_profile)
        await db.commit()
        await db.refresh(staff_profile)

        return CreateStaffUserProfile(**staff_profile)
    except Exception as e:
        raise e


async def update_company_profile(
    db: AsyncSession, data: UpdateCompanyProfile, current_user: User
) -> CreateCompanyProfileResponse:
    # Get the profile
    stmt = select(CompanyProfile).where(
        CompanyProfile.company_id == current_user.id)
    result = await db.execute(stmt)
    company_profile = result.scalar_one_or_none()

    if not company_profile:
        raise "No profile exists for this company"

    # Update values that are provided
    if company_profile:
        # Check if company name of phone number is already taken by another user
        stmt = select(CompanyProfile).where(
            CompanyProfile.company_name == data.company_name,
            CompanyProfile.phone_number == data.phone_number,
            User.id != current_user.id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise "Company name or phone number already registered"
        company_profile.company_name = data.company_name
        company_profile.address = data.address
        company_profile.phone_number = data.phone_number

    # Save changes
    await db.commit()
    await db.refresh(company_profile)

    return company_profile


async def update_company_payment_gateway(
    db: AsyncSession, data: UpdateCompanyPaymentGateway, current_user: User
) -> dict:
    # Get the profile
    stmt = select(CompanyProfile).where(
        CompanyProfile.company_id == current_user.id)
    result = await db.execute(stmt)
    company_profile = result.scalar_one_or_none()

    if not company_profile:
        raise "No profile exists for this company"

    # Update values that are provided
    if company_profile:
        company_profile.api_key = data.api_key
        company_profile.api_secret = data.api_secret
        company_profile.payment_gateway = data.payment_gateway

    # Save changes
    await db.commit()
    await db.refresh(company_profile)

    return {"message": "Payment gateway information updated"}

import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_models import Permission, Role, UserProfile, CompanyProfile, User

from app.schemas.profile_schema import (
    CreateCompanyProfile,
    CreateStaffUserProfile,
    CreateUserProfileBase,
    CreateCompanyProfileResponse,
    MessageResponse,
    UpdateCompanyPaymentGateway,
    UpdateCompanyProfile,
)
from app.schemas.user_schema import ActionEnum, ResourceEnum, StaffRoleCreate
from app.utils.utils import encrypt_data


def generate_permission(action: ActionEnum, resource: ResourceEnum) -> str:
    return f"{action.value}_{resource.value}"


async def pre_create_permissions(db: AsyncSession):
    # Fetch existing permissions from the database
    result = await db.execute(select(Permission.name))
    existing_permissions = set(result.scalars().all())

    permissions = []
    for action in ActionEnum:
        for resource in ResourceEnum:
            permission_name = generate_permission(action, resource)
            if permission_name not in existing_permissions:  # Check if permission already exists
                permissions.append({
                    "name": permission_name,
                    "description": f"Allows {action.value}ing {resource.value}",
                })

    # Add new permissions to the database
    if permissions:
        for perm in permissions:
            db.add(Permission(**perm))
        await db.commit()
        print(f"Added {len(permissions)} new permissions to the database.")
    else:
        print("No new permissions to add.")


async def create_company_profile(
    db: AsyncSession, data: CreateCompanyProfile, current_user: User
) -> CreateCompanyProfileResponse:
    try:
        # Create Profile
        company_profile = CompanyProfile(
            company_name=data.company_name,
            phone_number=data.phone_number,
            address=data.address,
            api_key=encrypt_data(data.api_key),
            api_secret=encrypt_data(data.api_secret),
            payment_gateway=data.payment_gateway,
            company_id=current_user.id,
        )

        # Add profile to database
        db.add(company_profile)
        await db.commit()
        await db.refresh(company_profile)

        return company_profile
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

        return guest_profile
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

        return staff_profile
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
) -> MessageResponse:
    # Get the profile
    stmt = select(CompanyProfile).where(
        CompanyProfile.company_id == current_user.id)
    result = await db.execute(stmt)
    company_profile = result.scalar_one_or_none()

    if not company_profile:
        raise Exception("No profile exists for this company")

    # Update values that are provided
    if company_profile:
        company_profile.api_key = encrypt_data(data.api_key)
        company_profile.api_secret = encrypt_data(data.api_secret)
        company_profile.payment_gateway = data.payment_gateway

    # Save changes
    await db.commit()
    await db.refresh(company_profile)

    msg = {"message": "Payment gateway information updated"}

    return MessageResponse(**msg)


async def create_staff_role(data: StaffRoleCreate, current_user: User, db: AsyncSession):
    try:
        # Create Role
        staff_role = Role(
            name=data.name,
            company_id=current_user.id,
            created_at=datetime.datetime.now()
        )

        # Add role to database
        db.add(staff_role)
        await db.commit()
        await db.refresh(staff_role)

        return staff_role
    except Exception as e:
        raise e

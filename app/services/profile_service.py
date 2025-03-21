import datetime
from fastapi import HTTPException, status
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
from app.schemas.user_schema import ActionEnum, AddPermissionsToRole, PermissionResponse, ResourceEnum, RoleCreateResponse, RolePermissionResponse, StaffRoleCreate, UserType
from app.utils.utils import encrypt_data


def generate_permission(action: ActionEnum, resource: ResourceEnum) -> str:
    return f"{action.value}_{resource.value}"


async def get_permission_by_name(name: str, db: AsyncSession):
    result = await db.execute(select(Permission).where(Permission.name == name))
    permission = result.scalar_one_or_none()
    permission_dict = {
        'id': permission.id,
        'name': permission.name,
        'description': permission.description
    }
    return permission_dict


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


def has_permission(user: User, required_permission: str) -> bool:
    # Fetch the user's role and permissions
    if not user.role:
        return False
    return required_permission in user.role.user_permissions


async def check_permission(user: User, required_permission: str):
    if not has_permission(user, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {required_permission}",
        )


async def assign_role_to_user(
    user_id: str,
    role_id: int,
    db: AsyncSession
) -> MessageResponse:

    # Fetch the user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the role
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Assign the role to the user
    user.role_id = role_id
    await db.commit()

    return {"message": "Role assigned to user"}

# async def check_permission(user: User, action: ActionEnum, resource: ResourceEnum):
#     required_permission = generate_permission(action, resource)
#     if not has_permission(user, required_permission):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=f"Permission denied: {required_permission}",
#         )


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


async def create_staff_role(data: StaffRoleCreate, current_user: User, db: AsyncSession) -> RoleCreateResponse:
    if current_user.user_type != UserType.COMPANY:
        raise Exception('Permission denied! Company admin only')
    try:
        # Create Role
        staff_role = Role(
            name=data.name.lower(),
            company_id=current_user.id,
            created_at=datetime.datetime.now()
        )

        # Add role to database
        db.add(staff_role)
        await db.commit()
        await db.refresh(staff_role)

        return {
            "id": staff_role.id,
            "name": staff_role.name,
            "company_id": staff_role.company_id,
            # "user_permissions": staff_role.user_permissions or []
        }

    except Exception as e:
        error_detail = str(e)
        if "UniqueViolationError" in error_detail and "roles_name_key" in error_detail:
            # Extract the key and value from the error message
            import re
            key_match = re.search(r"Key \((\w+)\)=\((\w+)\)", error_detail)
            if key_match:
                key, value = key_match.groups()
                raise Exception(
                    f"A role with this {key} '{value}' already exists for this company")


async def update_role_with_permissions(role_id: int,
                                       db: AsyncSession, data: AddPermissionsToRole, current_user: User
                                       ) -> RolePermissionResponse:
    # Get the profile
    stmt = select(Role).where(Role.company_id ==
                              current_user.id, Role.id == role_id)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    if not role:
        raise Exception("No role exists for this company")

    permissions = []
    for permission in data.permissions:
        permissions.append(await get_permission_by_name(name=permission, db=db))
        print(await get_permission_by_name(name=permission, db=db), '==========================')
        print(permission, '=======================')

    # Update values that are provided
    role.user_permissions = permissions

    # Save changes
    await db.commit()
    await db.refresh(role)

    return role


async def get_all_permissions(db: AsyncSession) -> list[PermissionResponse]:
    result = await db.execute(select(Permission))
    return result.scalars().all()


async def get_company_staff_role(role_id: int, db: AsyncSession, current_user: User) -> RoleCreateResponse:
    result = await db.execute(select(Role).where(Role.company_id == current_user.id, Role.id == role_id))
    return result.scalar_one_or_none()


async def get_all_company_staff_roles(db: AsyncSession, current_user: User) -> list[RoleCreateResponse]:
    result = await db.execute(select(Role).where(Role.company_id == current_user.id))
    return result.scalars().all()

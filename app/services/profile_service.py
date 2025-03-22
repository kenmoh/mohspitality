import datetime
import re
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_models import Department, NoPost, Outlet, Permission, Role, UserProfile, CompanyProfile, User

from app.schemas.profile_schema import (
    CreateCompanyProfile,
    CreateStaffUserProfile,
    CreateUserProfileBase,
    CreateCompanyProfileResponse,
    MessageResponse,
    UpdateCompanyPaymentGateway,
    UpdateCompanyProfile,
)
from app.schemas.room_schema import NoPostCreate, NoPostResponse
from app.schemas.user_schema import ActionEnum, AddPermissionsToRole, DepartmentCreate, DepartmentResponse, PermissionResponse, ResourceEnum, RoleCreateResponse, RolePermissionResponse, StaffRoleCreate, UserType
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


async def setup_company_roles(db: AsyncSession):
    """
    Set up default roles and permissions for a newly created company.

    Args:
        db: Database session
        company_user: The company user for which to create roles

    Returns:
        List of created roles
    """

    action_resource_list = [
        f"{action.value}_{resource.value}"
        for action in ActionEnum
        for resource in ResourceEnum
    ]

    # Create the role
    company_role = Role(
        company_id='88153ffc066511f09f975bcc15c457cb',
        name='company-admin',
        user_permissions=action_resource_list
    )

    db.add(company_role)
    await db.commit()
    await db.refresh(company_role)

    return company_role


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
                    "description": f"{action.value} {resource.value}",
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
    if not user.role or not user.role.user_permissions:
        return False

    # Check if the required_permission matches any permission name in the list
    return any(perm.get("name") == required_permission for perm in user.role.user_permissions)


async def check_permission(user: User, required_permission: str):
    if not has_permission(user, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {required_permission}",
        )


async def get_role_by_name(role_name: str,  db: AsyncSession, current_user: User | None = None):

    if current_user:
        stmt = select(Role).where((Role.name == role_name) &
                                  (Role.company_id == current_user.id))
        role = await db.execute(stmt)
        return role.scalar_one_or_none()
    else:
        stmt = select(Role).where(Role.name == role_name)
        role = await db.execute(stmt)
        return role.scalar_one_or_none()


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

        }

    except Exception as e:
        error_detail = str(e)

        if "UniqueViolationError" in error_detail and "role_name" in error_detail:
            # Extract the key and value from the error message
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


async def create_department(current_user: User, data: DepartmentCreate, db: AsyncSession):
    await check_permission(current_user, required_permission='create_departments')

    try:
        # Create Role
        department = Department(
            name=data.name.lower(),
            company_id=current_user.id,
        )

        # Add role to database
        db.add(department)
        await db.commit()
        await db.refresh(department)

        return department

    except Exception as e:
        error_detail = str(e)

        if "department_name" in error_detail:
            # Extract the key and value from the error message
            key_match = re.search(r"Key \((\w+)\)=\((\w+)\)", error_detail)
            if key_match:
                key, value = key_match.groups()
                raise Exception(
                    f"A department with this {key} '{value}' already exists for this company")


async def get_company_departments(current_user: User, db: AsyncSession) -> list[DepartmentResponse]:

    company_id = current_user.id if current_user.user_type == UserType.COMPANY else current_user.company_id
    stmt = select(Department).where(Department.company_id == company_id)
    result = await db.execute(stmt)
    departments = result.all()

    return departments


async def delete_company_department(department_id: int, current_user: User, db: AsyncSession) -> None:
    # Check permission
    await check_permission(current_user, required_permission='delete_departments')

    # Determine company ID
    company_id = current_user.id if current_user.user_type == UserType.COMPANY else current_user.company_id

    # Find the department
    stmt = select(Department).where(
        (Department.company_id == company_id) &
        (Department.id == department_id)
    )
    result = await db.execute(stmt)
    department = result.scalar_one_or_none()

    # Check if department exists
    if not department:
        raise HTTPException(
            status_code=404,
            detail=f"Department with ID {department_id} not found"
        )

    # Delete the department
    await db.delete(department)
    await db.commit()

    return None


async def create_no_post_list(data: NoPostCreate, current_user: User, db: AsyncSession) -> NoPostResponse:

    company_id = current_user.id if current_user.user_type == UserType.COMPANY else current_user.company_id
    no_post_list = NoPost(
        no_post_list=data.name.lower(),
        company_id=company_id,
    )

    stmt = select(NoPost).where(NoPost.company_id == company_id)
    existing = await db.execute(stmt)
    existing_record = existing.scalar_one_or_none()

    if existing_record:
        # Update the existing record
        existing_record.no_post_list = data.no_post_list
        # If you have other fields to update, add them here

        await db.commit()
        await db.refresh(existing_record)
        return existing_record
    else:
        # Create a new record
        no_post_list = NoPost(
            no_post_list=data.no_post_list,
            company_id=company_id,
        )

        db.add(no_post_list)
        await db.commit()
        await db.refresh(no_post_list)

        return no_post_list


async def get_company_no_post_list(current_user: User, db: AsyncSession) -> list[DepartmentResponse]:
    company_id = current_user.id if current_user.user_type == UserType.COMPANY else current_user.company_id
    stmt = select(NoPost).where(NoPost.company_id == company_id)
    result = await db.execute(stmt)
    no_post_list = result.all()

    return no_post_list


async def create_outlet(current_user: User, data: DepartmentCreate, db: AsyncSession):
    await check_permission(current_user, required_permission='create_outlets')

    try:

        outlet = Outlet(
            name=data.name.lower(),
            company_id=current_user.id,
        )

        # Add outlet to database
        db.add(outlet)
        await db.commit()
        await db.refresh(outlet)

        return outlet

    except Exception as e:
        error_detail = str(e)

        if "outlet_name" in error_detail:
            # Extract the key and value from the error message
            key_match = re.search(r"Key \((\w+)\)=\((\w+)\)", error_detail)
            if key_match:
                key, value = key_match.groups()
                raise Exception(
                    f"Outlet with this {key} '{value}' already exists for this company")


async def get_company_outlets(current_user: User, db: AsyncSession) -> list[DepartmentResponse]:
    company_id = current_user.id if current_user.user_type == UserType.COMPANY else current_user.company_id
    stmt = select(Outlet).where(Outlet.company_id == company_id)
    result = await db.execute(stmt)
    outlets = result.all()

    return outlets


async def delete_company_outlet(outlet_id: int, current_user: User, db: AsyncSession) -> None:
    # Check permission
    await check_permission(current_user, required_permission='delete_outlets')

    # Determine company ID
    company_id = current_user.id if current_user.user_type == UserType.COMPANY else current_user.company_id

    # Find the outlet
    stmt = select(Outlet).where(
        (Outlet.company_id == company_id) &
        (Outlet.id == outlet_id)
    )
    result = await db.execute(stmt)
    outlet = result.scalar_one_or_none()

    # Check if outlet exists
    if not outlet:
        raise HTTPException(
            status_code=404,
            detail=f"Outlet with ID {outlet_id} not found"
        )

    # Delete the outlet
    await db.delete(outlet)
    await db.commit()

    return None

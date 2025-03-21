from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database.db import get_db
from app.models.user_models import User
from app.schemas.profile_schema import (
    CreateCompanyProfile,
    CreateCompanyProfileResponse,
    CreateStaffUserProfile,
    CreateUserProfileBase,
    MessageResponse,
    UpdateCompanyPaymentGateway,
    UpdateCompanyProfile,
)
from app.schemas.user_schema import AddPermissionsToRole, AssignRoleToStaff, PermissionResponse, RoleCreateResponse, StaffRoleCreate
from app.services import profile_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/compnay-profile", status_code=status.HTTP_201_CREATED)
async def create_company_profile(
    data: CreateCompanyProfile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CreateCompanyProfileResponse:
    try:
        return await profile_service.create_company_profile(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/guest-profile",  status_code=status.HTTP_201_CREATED)
async def create_guest_profile(
    data: CreateUserProfileBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CreateUserProfileBase:
    try:
        return await profile_service.create_guest_profile(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/staff-profile", status_code=status.HTTP_201_CREATED)
async def create_staff_profile(
    data: CreateStaffUserProfile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CreateStaffUserProfile:
    try:
        return await profile_service.create_staff_profile(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/staff-role", status_code=status.HTTP_201_CREATED)
async def create_staff_role(
    data: StaffRoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoleCreateResponse:
    try:
        return await profile_service.create_staff_role(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/all-company-roles")
async def get_all_company_staff_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)

) -> list[RoleCreateResponse]:
    try:
        return await profile_service.get_all_company_staff_roles(db=db, current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{role_id}/company-role")
async def role_details(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)

) -> RoleCreateResponse:
    try:
        return await profile_service.get_company_staff_role(role_id=role_id, db=db, current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{role_id}/company-role", status_code=status.HTTP_202_ACCEPTED)
async def update_role_permission(
    role_id: int,
    data: AddPermissionsToRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)

) -> RoleCreateResponse:
    try:
        return await profile_service.update_role_with_permissions(role_id=role_id, data=data, db=db, current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/assign-role-to-staff", status_code=status.HTTP_202_ACCEPTED)
async def assign_role_to_staff(
    user_id: str,
    data: AssignRoleToStaff,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)

) -> RoleCreateResponse:
    try:
        return await profile_service.assign_role_to_user(user_id=user_id, data=data, db=db, current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/all-permissions")
async def get_all_permissions(
    db: AsyncSession = Depends(get_db),

) -> list[PermissionResponse]:
    try:
        return await profile_service.get_all_permissions(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/company-profile-update",  status_code=status.HTTP_202_ACCEPTED)
async def update_company_profile(
    data: UpdateCompanyProfile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CreateCompanyProfileResponse:
    try:
        return await profile_service.update_company_profile(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/company-payment-gateway-update", status_code=status.HTTP_202_ACCEPTED)
async def update_company_payment_gateway(
    data: UpdateCompanyPaymentGateway,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:

    try:
        return await profile_service.update_company_payment_gateway(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))

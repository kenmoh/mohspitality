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
from app.services import profile_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/compnay-profile", status_code=status.HTTP_201_CREATED)
async def create_company_profile(
    data: CreateCompanyProfile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CreateCompanyProfileResponse:
    try:
        await profile_service.create_company_profile(
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
        await profile_service.create_guest_profile(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/staff-profile")
async def create_staff_profile(
    data: CreateStaffUserProfile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CreateStaffUserProfile:
    try:
        await profile_service.create_staff_profile(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/company-profile-update",  status_code=status.HTTP_202_ACCEPTED)
async def update_company_profile(
    data: UpdateCompanyProfile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CreateCompanyProfileResponse:
    try:
        await profile_service.update_company_profile(
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
        await profile_service.update_company_payment_gateway(
            db=db, data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))

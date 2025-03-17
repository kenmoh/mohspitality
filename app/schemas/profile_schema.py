from pydantic import BaseModel

from app.schemas.user_schema import PaymentGatwayEnum


class CreateUserProfileBase(BaseModel):
    full_name: str
    phone_number: str


class CreateStaffUserProfile(CreateUserProfileBase):
    department: str


class CreateCompanyProfile(BaseModel):
    company_name: str
    phone_number: str
    address: str
    api_key: str
    api_secret: str
    payment_gateway: PaymentGatwayEnum


class UpdateCompanyProfile(BaseModel):
    company_name: str
    phone_number: str
    address: str


class UpdateCompanyPaymentGateway(BaseModel):
    api_key: str
    api_secret: str
    payment_gateway: PaymentGatwayEnum


class CreateCompanyProfileResponse(BaseModel):
    company_id: str
    company_name: str
    phone_number: str
    address: str
    logo_url: str | None = None

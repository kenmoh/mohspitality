from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class OutletType(str, Enum):
    RESTAURANT = "restaurant"
    ROOM_SERVICE = "room_service"


class NoPostCreate(BaseModel):
    no_post_list: str


class NoPostResponse(NoPostCreate):
    id: int
    company_id: str
    created_at: datetime
    updated_at: datetime


class OutletCreate(BaseModel):
    name: str


class OutletResponse(OutletCreate):
    id: int
    company_id: str
    created_at: datetime


class QRCodeCreate(BaseModel):
    room_or_table_numbers: str
    fill_color: str | None = None
    back_color: str | None = None
    outlet_type: OutletType


class QRCodeResponse(QRCodeCreate):
    id: int
    company_id: str
    created_at: datetime
    updated_at: datetime

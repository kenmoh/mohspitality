from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel


class ItemCategory(str, Enum):
    FOOD = "food"
    BEVERAGE = "beverage"
    LINEN = "linen"


class CreateItemSchema(BaseModel):
    name: str
    description: str
    unit: str
    reorder_point: int
    price: Decimal
    image_url: str
    category: ItemCategory


class CreateItemReturnSchema(CreateItemSchema):
    id: int


class ItemStockSchema(BaseModel):
    quantity: int
    notes: str | None = None


class ItemStockReturnSchema(ItemStockSchema):
    id: int
    created_at: datetime


class InventorySchecma(BaseModel):
    id: int
    name: str
    quantity: int
    unit: str
    reorder_point: int
    price: Decimal
    image_url: str
    category: ItemCategory
    description: str
    stocks: list[ItemStockSchema]

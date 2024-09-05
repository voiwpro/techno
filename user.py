import argparse
from pydantic import BaseModel, Field, EmailStr, ValidationError, field_validator
from typing import List, Optional
from datetime import datetime, date
from pydantic.dataclasses import dataclass
from dataclasses import asdict
import json

class User(BaseModel):
    id: int = Field(..., gt=0, description="User ID")
    name: str = Field(..., min_length=2, max_length=50, description="User name")
    email: EmailStr = Field(..., description="User email")
    age: int = Field(..., ge=18, le=120, description="User age")
    tags: List[str] = Field(default_factory=list, description="User tags")

    @field_validator('name')
    def name_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()

class Product(BaseModel):
    id: int = Field(..., gt=0, description="Product ID")
    name: str = Field(..., min_length=3, max_length=50, description="Product name")
    price: float = Field(..., ge=0, description="Product price")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    in_stock: bool = Field(default=True, description="Product in stock")
    created_at: Optional[str] = Field(None, description="Product creation date")
    expiry_date: Optional[str] = Field(None, description="Product expiry date")

    @field_validator('price')
    def price_must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price must be non-negative")
        return round(v, 2)

@dataclass
class ProductData:
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=3, max_length=50)
    price: float = Field(..., ge=0)
    tags: List[str] = Field(default_factory=list)
    in_stock: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    expiry_date: Optional[date] = None

class UserData(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    age: int = Field(..., ge=18, le=120)
    created_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)

    @field_validator('name')
    def name_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def add_model(parser, model):
    fields = model.__fields__
    for name, field in fields.items():
        if not any(arg.dest == name for arg in parser._actions):
            parser.add_argument(
                f"--{name}",  
                type=str if field.annotation == EmailStr else field.annotation,  # Ensure email is parsed as str
                default=field.default if field.default is not None else argparse.SUPPRESS,
                help=field.description if field.description else "",
            )

def main():
    parser = argparse.ArgumentParser(description="Process some data.")
    # Add Product and User to the parser
    add_model(parser, Product)
    add_model(parser, User)

    # Parse the command-line arguments
    args = parser.parse_args()

    # Validate and parse arguments using Pydantic
    try:
        product_args = Product(**vars(args))
        user_args = User(**vars(args))
    except ValidationError as e:
        print("Argument Validation Error:", e)
        return

    # Parse dates
    product_created_at = datetime.fromisoformat(product_args.created_at) if product_args.created_at else datetime.now()
    product_expiry_date = date.fromisoformat(product_args.expiry_date) if product_args.expiry_date else None

    # Create Product
    try:
        product = ProductData(
            id=product_args.id,
            name=product_args.name,
            price=product_args.price,
            tags=product_args.tags,
            in_stock=product_args.in_stock,
            created_at=product_created_at,
            expiry_date=product_expiry_date
        )
        print("Valid Product:", product)
        print("JSON:", json.dumps(asdict(product), cls=DateTimeEncoder))
    except ValidationError as e:
        print("Validation Error:", e)

    # Create User
    try:
        user = UserData(
            id=user_args.id,
            name=user_args.name,
            email=user_args.email,
            age=user_args.age,
            tags=user_args.tags
        )
        json_data = user.model_dump_json()
        print("Serialized JSON:", json_data)

        deserialized_user = UserData.model_validate_json(json_data)
        print("Deserialized user:", deserialized_user)
    except ValidationError as e:
        print("Validation Error:", e)

if __name__ == "__main__":
    main()
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerRead

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    """Creates a new customer entry."""
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=List[CustomerRead])
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieves all customers with pagination."""
    return db.query(Customer).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=CustomerRead)
def get_customer(id: int, db: Session = Depends(get_db)):
    """Retrieves a single customer by primary ID."""
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

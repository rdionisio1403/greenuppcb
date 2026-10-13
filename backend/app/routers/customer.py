from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_csrf
from app.models.customer import Customer
from app.models.pcb import PCB
from app.schemas.customer import CustomerCreate, CustomerRead

router = APIRouter(prefix="/customers", tags=["Customers"])


def get_accessible_customer(id: int, db: Session, current_user):
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if current_user.role != "admin" and customer.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Customer access denied")
    return customer


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    """Creates a new customer entry."""
    if not data.name.strip():
        raise HTTPException(status_code=422, detail="Customer name is required")
    customer = Customer(
        name=data.name.strip(),
        contact_info=data.contact_info,
        reference=data.reference,
        created_by_user_id=current_user.id,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=List[CustomerRead])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieves customers with pagination."""
    query = db.query(Customer)
    if current_user.role != "admin":
        query = query.filter(Customer.created_by_user_id == current_user.id)
    return query.offset(skip).limit(min(limit, 500)).all()


@router.get("/{id}", response_model=CustomerRead)
def get_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieves a single customer."""
    return get_accessible_customer(id, db, current_user)


@router.put("/{id}", response_model=CustomerRead)
def update_customer(
    id: int,
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    """Updates an accessible customer."""
    customer = get_accessible_customer(id, db, current_user)
    if not data.name.strip():
        raise HTTPException(status_code=422, detail="Customer name is required")

    customer.name = data.name.strip()
    customer.contact_info = data.contact_info
    customer.reference = data.reference
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{id}", status_code=204)
def delete_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    """Deletes a customer only when no PCB records reference it."""
    customer = get_accessible_customer(id, db, current_user)

    linked_pcb = db.query(PCB.id).filter(PCB.customer_id == customer.id).first()
    if linked_pcb:
        raise HTTPException(
            status_code=409,
            detail="This customer is linked to PCB records and cannot be deleted. "
                   "Keep the customer to preserve historical records.",
        )

    db.delete(customer)
    db.commit()
    return None

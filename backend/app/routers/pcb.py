def compute_is_archived(pcb) -> bool:
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=365)
    if not pcb.tests:
        return False
    # If all tests are older than 1 year, the card is archived
    return all(t.test_date and t.test_date < cutoff for t in pcb.tests)

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.customer import Customer
from app.schemas.pcb import PCBCreate, PCBRead, PCBDetailRead, PCBUpdate

router = APIRouter(prefix="/pcbs", tags=["PCBs"])


@router.post("", response_model=PCBRead, status_code=201)
def create_pcb(data: PCBCreate, db: Session = Depends(get_db)):
    existing = db.query(PCB).filter(PCB.internal_reference == data.internal_reference).first()
    if existing:
        raise HTTPException(status_code=409, detail="Internal reference already exists")

    pcb_dict = data.model_dump()
    
    # Match customer by ID or resolve dynamically by customer name
    if pcb_dict.get("customer_id"):
        cust = db.query(Customer).filter(Customer.id == pcb_dict["customer_id"]).first()
        if cust:
            pcb_dict["customer_name"] = cust.name
    elif pcb_dict.get("customer_name"):
        c_name = pcb_dict["customer_name"].strip()
        cust = db.query(Customer).filter(Customer.name.ilike(c_name)).first()
        if not cust:
            # Register newly encountered client in customers registry
            cust = Customer(name=c_name)
            db.add(cust)
            db.flush()
        pcb_dict["customer_id"] = cust.id
        pcb_dict["customer_name"] = cust.name

    pcb = PCB(**pcb_dict)
    db.add(pcb)
    db.commit()
    db.refresh(pcb)
    return pcb


@router.get("", response_model=List[PCBRead])
def list_pcbs(q: str | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(PCB)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                PCB.internal_reference.ilike(pattern),
                PCB.customer_name.ilike(pattern),
                PCB.pcb_model.ilike(pattern),
                PCB.equipment.ilike(pattern),
            )
        )
    return query.order_by(PCB.id.desc()).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=PCBDetailRead)
def get_pcb(id: int, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")
    return pcb


@router.patch("/{id}", response_model=PCBRead)
def update_pcb(id: int, data: PCBUpdate, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    update_data = data.model_dump(exclude_unset=True)

    if "internal_reference" in update_data and update_data["internal_reference"] != pcb.internal_reference:
        existing = db.query(PCB).filter(PCB.internal_reference == update_data["internal_reference"]).first()
        if existing:
            raise HTTPException(status_code=409, detail="Internal reference already exists")

    if "customer_id" in update_data and update_data["customer_id"]:
        cust = db.query(Customer).filter(Customer.id == update_data["customer_id"]).first()
        if cust:
            update_data["customer_name"] = cust.name

    for field, value in update_data.items():
        setattr(pcb, field, value)

    db.commit()
    db.refresh(pcb)
    return pcb

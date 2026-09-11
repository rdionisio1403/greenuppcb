from typing import List, Optional
from datetime import datetime, timezone, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, cast, String, func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.customer import Customer
from app.schemas.pcb import PCBCreate, PCBRead, PCBDetailRead, PCBUpdate, PCBStatus, PaginatedPCBRead

router = APIRouter(prefix="/pcbs", tags=["PCBs"])


def compute_is_archived(pcb) -> bool:
    if not getattr(pcb, "tests", None):
        return False
    
    # 365 days threshold
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    
    has_test = False
    for t in pcb.tests:
        has_test = True
        t_date = getattr(t, "test_date", None)
        if not t_date:
            return False
        
        # Convert date to datetime if needed
        if isinstance(t_date, date) and not isinstance(t_date, datetime):
            t_date = datetime.combine(t_date, datetime.min.time())
        
        if t_date.tzinfo is None:
            t_date = t_date.replace(tzinfo=timezone.utc)
            
        if t_date >= cutoff:
            return False
            
    return has_test


def normalize_pcb(pcb):
    # Set dynamic is_archived field on the model instance
    setattr(pcb, "is_archived", compute_is_archived(pcb))
    
    # Ensure legacy lower-case status values map cleanly to PCBStatus
    if pcb.status:
        val = pcb.status.upper()
        if val == "RECEIVED":
            val = "REGISTERED"
        if val in PCBStatus.__members__:
            pcb.status = PCBStatus[val].value
        else:
            pcb.status = PCBStatus.REGISTERED.value
    else:
        pcb.status = PCBStatus.REGISTERED.value
    return pcb


@router.post("", response_model=PCBRead, status_code=201)
def create_pcb(data: PCBCreate, db: Session = Depends(get_db)):
    existing = db.query(PCB).filter(PCB.internal_reference == data.internal_reference).first()
    if existing:
        raise HTTPException(status_code=409, detail="Internal reference already exists")

    pcb_dict = data.model_dump()
    
    if pcb_dict.get("customer_id"):
        cust = db.query(Customer).filter(Customer.id == pcb_dict["customer_id"]).first()
        if cust:
            pcb_dict["customer_name"] = cust.name
    elif pcb_dict.get("customer_name"):
        c_name = pcb_dict["customer_name"].strip()
        cust = db.query(Customer).filter(Customer.name.ilike(c_name)).first()
        if not cust:
            cust = Customer(name=c_name)
            db.add(cust)
            db.flush()
        pcb_dict["customer_id"] = cust.id
        pcb_dict["customer_name"] = cust.name

    pcb = PCB(**pcb_dict)
    db.add(pcb)
    db.commit()
    db.refresh(pcb)
    return normalize_pcb(pcb)


@router.get("", response_model=PaginatedPCBRead)
def list_pcbs(
    q: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(PCB)
    if q and q.strip():
        term = q.strip()
        pat = f"%{term}%"
        clean_term = term.lower().replace(" ", "_")
        status_str = func.lower(cast(PCB.status, String))
        status_spaces = func.replace(status_str, "_", " ")
        filters = [
            PCB.internal_reference.ilike(pat),
            PCB.serial_number.ilike(pat),
            PCB.customer_name.ilike(pat),
            PCB.pcb_model.ilike(pat),
            PCB.equipment.ilike(pat),
            status_str.ilike(f"%{clean_term}%"),
            status_spaces.ilike(pat),
            cast(PCB.date_received, String).ilike(pat),
        ]

        # Kullanici a, ar, arc, archive veya archived yazdikca eslestir
        t_low = term.lower()
        if len(t_low) >= 2 and ("archived".startswith(t_low) or "archive".startswith(t_low) or "archiv" in t_low):
            all_pcbs = db.query(PCB).all()
            archived_ids = [p.id for p in all_pcbs if compute_is_archived(p)]
            if archived_ids:
                filters.append(PCB.id.in_(archived_ids))

        query = query.filter(or_(*filters))

    total = query.count()
    offset_val = max(0, (page - 1) * limit)
    pcbs = query.order_by(PCB.id.desc()).offset(offset_val).limit(limit).all()
    
    total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1

    return {
        "items": [normalize_pcb(p) for p in pcbs],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


@router.get("/{id}", response_model=PCBDetailRead)
def get_pcb(id: int, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")
    return normalize_pcb(pcb)


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
    return normalize_pcb(pcb)

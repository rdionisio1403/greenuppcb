import os
import uuid
from io import BytesIO
from enum import Enum
from typing import List
from PIL import Image as PILImage

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.image import Image
from app.schemas.image import ImageRead


class ImageCategory(str, Enum):
    BEFORE = "before"
    DURING = "during"
    AFTER = "after"
    DEFECT = "defect"


router = APIRouter(prefix="/pcbs/{pcb_id}/images", tags=["Images"])

UPLOAD_DIR = "/opt/greenupcb/backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def process_and_save_image(file_bytes: bytes, filename_prefix: str) -> str:
    """Opens image, resizes to max 1920px width, and optimizes to WebP format."""
    with PILImage.open(BytesIO(file_bytes)) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        max_width = 1920
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * ratio)
            img = img.resize((max_width, new_height), PILImage.Resampling.LANCZOS)

        unique_filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.webp"
        save_path = os.path.join(UPLOAD_DIR, unique_filename)
        img.save(save_path, "WEBP", quality=80, optimize=True)

        return f"/uploads/{unique_filename}"


@router.post("", response_model=ImageRead, status_code=201)
async def upload_pcb_image(
    pcb_id: int,
    category: ImageCategory = Form(..., description="Allowed: before, during, after, defect"),
    file: UploadFile = File(..., description="Image file to upload"),
    db: Session = Depends(get_db)
):
    """Uploads and associates an inspection image with a PCB lifecycle stage."""
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    try:
        content = await file.read()
        filename_prefix = f"pcb_{pcb_id}_{category.value}"
        file_url = process_and_save_image(content, filename_prefix)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

    new_image = Image(
        pcb_id=pcb_id,
        category=category.value,
        filename_path=file_url
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


@router.get("", response_model=List[ImageRead])
def list_images(pcb_id: int, db: Session = Depends(get_db)):
    """Retrieves all inspection images associated with the specified PCB."""
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    return db.query(Image).filter(Image.pcb_id == pcb_id).all()

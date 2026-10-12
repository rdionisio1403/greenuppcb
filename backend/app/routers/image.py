import os
import uuid
from io import BytesIO
from enum import Enum
from typing import Optional, List
from PIL import Image as PILImage

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_csrf
from app.audit import log_audit
from app.models.pcb import PCB
from app.models.image import Image
from app.schemas.image import ImageRead


from pathlib import Path
class ImageCategory(str, Enum):
    BEFORE = "before"
    DURING = "during"
    AFTER = "after"
    DEFECT = "defect"


router = APIRouter(prefix="/pcbs/{pcb_id}/images", tags=["Images"])

UPLOAD_DIR = "/opt/greenupcb/backend/uploads"
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
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
    request: Request,
    pcb_id: int,
    category: ImageCategory = Form(..., description="Allowed: before, during, after, defect"),
    technician: str = Form("Technician", description="Technician who uploaded the image"),
    test_id: Optional[int] = Form(None, description="Optional associated test ID"),
    file: UploadFile = File(..., description="Image file to upload"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    """Uploads and associates an inspection image with a PCB lifecycle stage."""
    from app.routers.pcb import compute_is_archived

    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")
    if compute_is_archived(pcb):
        raise HTTPException(
            status_code=409,
            detail="Archived PCB records cannot be modified.",
        )

    # Validate test association and enforce tester attribution
    if test_id is not None:
        test = db.query(Test).filter(Test.id == test_id).first() if "Test" in globals() else None
        if not test:
            from app.models.test import Test
            test = db.query(Test).filter(Test.id == test_id).first()
        if not test or test.pcb_id != pcb_id:
            raise HTTPException(
                status_code=400,
                detail=f"Test with ID {test_id} does not exist or does not belong to PCB #{pcb_id}"
            )
        # Strict Validation: Reject if specified technician does not match the test executor
        if test.tester and technician and technician.strip().lower() != test.tester.strip().lower():
            raise HTTPException(
                status_code=400,
                detail=f"Technician mismatch: Test #{test_id} was conducted by '{test.tester}', but '{technician}' was provided."
            )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_extension = Path(file.filename or "").suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image file extension. Allowed: .jpg, .jpeg, .png, .webp",
        )

    try:
        content = await file.read(MAX_IMAGE_SIZE + 1)

        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image file is too large. Maximum allowed size is 10 MB.",
            )

        filename_prefix = f"pcb_{pcb_id}_{category.value}"
        file_url = process_and_save_image(content, filename_prefix)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

    new_image = Image(
        pcb_id=pcb_id,
        category=category.value,
        technician=technician,
        test_id=test_id,
        filename_path=file_url
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    log_audit(
        db=db,
        event_type="IMAGE_UPLOADED",
        request=request,
        user_id=current_user.id,
        details=f"image_id={new_image.id};pcb_id={pcb_id};category={category.value}",
    )

    return new_image


@router.get("", response_model=List[ImageRead])
def list_images(pcb_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Retrieves all inspection images associated with the specified PCB."""
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    return db.query(Image).filter(Image.pcb_id == pcb_id).all()


def _managed_upload_path(filename_path: str):
    """Resolve only files directly inside the configured uploads directory."""
    if not filename_path or not filename_path.startswith("/uploads/"):
        return None

    filename = Path(filename_path).name
    if not filename or filename in {".", ".."}:
        return None

    upload_root = Path(UPLOAD_DIR).resolve()
    candidate = (upload_root / filename).resolve()

    if candidate.parent != upload_root:
        return None

    return candidate


def _validate_image_test_link(db, pcb_id, test_id, technician):
    """Validate an optional test association and technician attribution."""
    if test_id is None:
        return

    from app.models.test import Test

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test or test.pcb_id != pcb_id:
        raise HTTPException(
            status_code=400,
            detail=f"Test with ID {test_id} does not belong to PCB #{pcb_id}.",
        )

    if (
        test.tester
        and technician
        and technician.strip().lower() != test.tester.strip().lower()
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Technician must match the executor of test #{test_id}.",
        )


async def _process_replacement_upload(file: UploadFile, pcb_id: int, category: ImageCategory):
    """Validate and store a replacement image without touching the old file."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image extension. Allowed: .jpg, .jpeg, .png, .webp.",
        )

    content = await file.read(MAX_IMAGE_SIZE + 1)
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image file is too large. Maximum allowed size is 10 MB.",
        )

    try:
        filename_path = process_and_save_image(
            content,
            f"pcb_{pcb_id}_{category.value}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file could not be processed as an image.",
        ) from exc

    return filename_path


@router.put("/{image_id}", response_model=ImageRead)
async def replace_pcb_image(
    request: Request,
    pcb_id: int,
    image_id: int,
    category: ImageCategory = Form(...),
    technician: str = Form("Technician"),
    test_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    """Replace an inspection image while preserving the old file until commit."""
    from app.routers.pcb import compute_is_archived

    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found.")
    if compute_is_archived(pcb):
        raise HTTPException(
            status_code=409,
            detail="Archived PCB records cannot be modified.",
        )

    image_record = (
        db.query(Image)
        .filter(Image.id == image_id, Image.pcb_id == pcb_id)
        .first()
    )
    if not image_record:
        raise HTTPException(status_code=404, detail="Image not found for this PCB.")

    _validate_image_test_link(db, pcb_id, test_id, technician)

    old_path = image_record.filename_path
    new_path = await _process_replacement_upload(file, pcb_id, category)

    try:
        image_record.category = category.value
        image_record.technician = technician
        image_record.test_id = test_id
        image_record.filename_path = new_path
        db.commit()
        db.refresh(image_record)
    except Exception:
        db.rollback()
        new_file = _managed_upload_path(new_path)
        if new_file and new_file.is_file():
            new_file.unlink()
        raise

    old_file = _managed_upload_path(old_path)
    if old_file and old_file.is_file() and old_file != _managed_upload_path(new_path):
        try:
            old_file.unlink()
        except OSError:
            # Keep the committed database record valid; an orphaned old file
            # can be cleaned up separately if filesystem permissions prevent removal.
            pass

    log_audit(
        db=db,
        event_type="IMAGE_UPDATED",
        request=request,
        user_id=current_user.id,
        details=f"image_id={image_record.id};pcb_id={pcb_id};category={category.value}",
    )

    return image_record


@router.delete("/{image_id}", status_code=204)
def delete_pcb_image(
    request: Request,
    pcb_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    """Delete an image record and its managed upload file."""
    from app.routers.pcb import compute_is_archived
    from fastapi import Response

    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found.")
    if compute_is_archived(pcb):
        raise HTTPException(
            status_code=409,
            detail="Archived PCB records cannot be modified.",
        )

    image_record = (
        db.query(Image)
        .filter(Image.id == image_id, Image.pcb_id == pcb_id)
        .first()
    )
    if not image_record:
        raise HTTPException(status_code=404, detail="Image not found for this PCB.")

    file_path = _managed_upload_path(image_record.filename_path)
    if file_path is None:
        raise HTTPException(
            status_code=400,
            detail="The image path is not inside the managed uploads directory.",
        )

    details = (
        f"image_id={image_record.id};pcb_id={pcb_id};"
        f"category={image_record.category}"
    )

    try:
        db.delete(image_record)
        db.commit()
    except Exception:
        db.rollback()
        raise

    if file_path.is_file():
        try:
            file_path.unlink()
        except OSError:
            # The database deletion has succeeded. Avoid restoring the record
            # or deleting any unrelated file if filesystem cleanup fails.
            pass

    log_audit(
        db=db,
        event_type="IMAGE_DELETED",
        request=request,
        user_id=current_user.id,
        details=details,
    )

    return Response(status_code=204)

"""API endpoints for user-defined custom catalog targets."""

import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalog_models import UserTarget

router = APIRouter(prefix="/targets/custom", tags=["custom-targets"])


def _name_to_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")
    return f"USER:{slug}"


class CustomTargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    ra_hours: float = Field(ge=0, lt=24)
    dec_degrees: float = Field(ge=-90, le=90)
    magnitude: Optional[float] = None
    size_arcmin: Optional[float] = None
    object_type: str = Field(default="other", max_length=50)
    notes: Optional[str] = None


class CustomTargetOut(BaseModel):
    id: int
    catalog_id: str
    name: str
    ra_hours: float
    dec_degrees: float
    magnitude: Optional[float]
    size_arcmin: Optional[float]
    object_type: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CustomTargetOut])
async def list_custom_targets(db: Session = Depends(get_db)):
    return db.query(UserTarget).order_by(UserTarget.created_at.desc()).all()


@router.post("/", response_model=CustomTargetOut, status_code=201)
async def create_custom_target(payload: CustomTargetCreate, db: Session = Depends(get_db)):
    catalog_id = _name_to_slug(payload.name)
    existing = db.query(UserTarget).filter(UserTarget.catalog_id == catalog_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"A target with catalog_id '{catalog_id}' already exists.")
    ut = UserTarget(
        catalog_id=catalog_id,
        name=payload.name,
        ra_hours=payload.ra_hours,
        dec_degrees=payload.dec_degrees,
        magnitude=payload.magnitude,
        size_arcmin=payload.size_arcmin,
        object_type=payload.object_type,
        notes=payload.notes,
    )
    db.add(ut)
    db.commit()
    db.refresh(ut)
    return ut


@router.put("/{target_id}", response_model=CustomTargetOut)
async def update_custom_target(target_id: int, payload: CustomTargetCreate, db: Session = Depends(get_db)):
    ut = db.query(UserTarget).filter(UserTarget.id == target_id).first()
    if not ut:
        raise HTTPException(status_code=404, detail=f"Custom target {target_id} not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ut, field, value)
    db.commit()
    db.refresh(ut)
    return ut


@router.delete("/{target_id}")
async def delete_custom_target(target_id: int, db: Session = Depends(get_db)):
    ut = db.query(UserTarget).filter(UserTarget.id == target_id).first()
    if not ut:
        raise HTTPException(status_code=404, detail=f"Custom target {target_id} not found.")
    db.delete(ut)
    db.commit()
    return {"message": f"Custom target {target_id} deleted."}

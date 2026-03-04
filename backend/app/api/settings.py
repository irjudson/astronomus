"""Settings API endpoints for application configuration."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings_models import DEFAULT_SETTINGS, AppSetting, ObservingLocation, SeestarDevice

router = APIRouter(prefix="/settings", tags=["settings"])


# ========================================================================
# Pydantic Schemas
# ========================================================================


class AppSettingCreate(BaseModel):
    key: str
    value: str
    value_type: str = "string"
    description: Optional[str] = None
    category: Optional[str] = None
    is_secret: bool = False


class AppSettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None


class AppSettingResponse(BaseModel):
    id: int
    key: str
    value: str
    value_type: str
    description: Optional[str]
    category: Optional[str]
    is_secret: bool

    class Config:
        from_attributes = True


class SeestarDeviceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    control_host: Optional[str] = None
    control_port: int = 4700
    is_control_enabled: bool = False
    mount_path: Optional[str] = None
    is_mount_enabled: bool = False
    is_default: bool = False


class SeestarDeviceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    control_host: Optional[str] = None
    control_port: Optional[int] = None
    is_control_enabled: Optional[bool] = None
    mount_path: Optional[str] = None
    is_mount_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class SeestarDeviceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    control_host: Optional[str]
    control_port: int
    is_control_enabled: bool
    mount_path: Optional[str]
    is_mount_enabled: bool
    is_default: bool
    is_active: bool

    class Config:
        from_attributes = True


class ObservingLocationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    elevation: float = 0.0
    timezone: str = "UTC"
    bortle_class: Optional[int] = Field(None, ge=1, le=9)
    is_default: bool = False


class ObservingLocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    elevation: Optional[float] = None
    timezone: Optional[str] = None
    bortle_class: Optional[int] = Field(None, ge=1, le=9)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class ObservingLocationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    latitude: float
    longitude: float
    elevation: float
    timezone: str
    bortle_class: Optional[int]
    is_default: bool
    is_active: bool

    class Config:
        from_attributes = True


# ========================================================================
# App Settings Endpoints
# ========================================================================


@router.get("/app", response_model=List[AppSettingResponse])
async def get_all_settings(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
):
    """Get all application settings, optionally filtered by category."""
    query = db.query(AppSetting)
    if category:
        query = query.filter(AppSetting.category == category)
    return query.all()


@router.get("/app/{key}", response_model=AppSettingResponse)
async def get_setting(key: str, db: Session = Depends(get_db)):
    """Get a specific setting by key."""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return setting


@router.put("/app/{key}", response_model=AppSettingResponse)
async def update_setting(key: str, update: AppSettingUpdate, db: Session = Depends(get_db)):
    """Update a setting value."""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    setting.value = update.value
    if update.description is not None:
        setting.description = update.description

    db.commit()
    db.refresh(setting)
    return setting


@router.post("/app", response_model=AppSettingResponse)
async def create_setting(setting: AppSettingCreate, db: Session = Depends(get_db)):
    """Create a new application setting."""
    existing = db.query(AppSetting).filter(AppSetting.key == setting.key).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Setting '{setting.key}' already exists")

    db_setting = AppSetting(**setting.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


@router.delete("/app/{key}")
async def delete_setting(key: str, db: Session = Depends(get_db)):
    """Delete a setting."""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    db.delete(setting)
    db.commit()
    return {"message": f"Setting '{key}' deleted"}


@router.post("/app/init")
async def initialize_default_settings(db: Session = Depends(get_db)):
    """Initialize default settings if they don't exist."""
    created = []
    for setting_data in DEFAULT_SETTINGS:
        existing = db.query(AppSetting).filter(AppSetting.key == setting_data["key"]).first()
        if not existing:
            db_setting = AppSetting(**setting_data)
            db.add(db_setting)
            created.append(setting_data["key"])

    db.commit()
    return {"message": f"Initialized {len(created)} settings", "created": created}


@router.get("/app/categories/list")
async def get_setting_categories(db: Session = Depends(get_db)):
    """Get list of all setting categories."""
    categories = db.query(AppSetting.category).distinct().all()
    return {"categories": [c[0] for c in categories if c[0]]}


# ========================================================================
# Seestar Device Endpoints
# ========================================================================


@router.get("/devices", response_model=List[SeestarDeviceResponse])
async def get_all_devices(
    active_only: bool = Query(True, description="Only return active devices"),
    db: Session = Depends(get_db),
):
    """Get all Seestar devices."""
    query = db.query(SeestarDevice)
    if active_only:
        query = query.filter(SeestarDevice.is_active == True)
    return query.all()


@router.get("/devices/{device_id}", response_model=SeestarDeviceResponse)
async def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get a specific device by ID."""
    device = db.query(SeestarDevice).filter(SeestarDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device


@router.get("/devices/default/get", response_model=SeestarDeviceResponse)
async def get_default_device(db: Session = Depends(get_db)):
    """Get the default Seestar device."""
    device = db.query(SeestarDevice).filter(SeestarDevice.is_default == True).first()
    if not device:
        raise HTTPException(status_code=404, detail="No default device configured")
    return device


@router.post("/devices", response_model=SeestarDeviceResponse)
async def create_device(device: SeestarDeviceCreate, db: Session = Depends(get_db)):
    """Create a new Seestar device."""
    existing = db.query(SeestarDevice).filter(SeestarDevice.name == device.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Device '{device.name}' already exists")

    # If this is set as default, unset other defaults
    if device.is_default:
        db.query(SeestarDevice).filter(SeestarDevice.is_default == True).update({"is_default": False})

    db_device = SeestarDevice(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.put("/devices/{device_id}", response_model=SeestarDeviceResponse)
async def update_device(device_id: int, update: SeestarDeviceUpdate, db: Session = Depends(get_db)):
    """Update a Seestar device."""
    device = db.query(SeestarDevice).filter(SeestarDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

    update_data = update.model_dump(exclude_unset=True)

    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(SeestarDevice).filter(SeestarDevice.is_default == True).update({"is_default": False})

    for key, value in update_data.items():
        setattr(device, key, value)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/devices/{device_id}")
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Delete a Seestar device."""
    device = db.query(SeestarDevice).filter(SeestarDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

    db.delete(device)
    db.commit()
    return {"message": f"Device '{device.name}' deleted"}


# ========================================================================
# Observing Location Endpoints
# ========================================================================


@router.get("/locations", response_model=List[ObservingLocationResponse])
async def get_all_locations(
    active_only: bool = Query(True, description="Only return active locations"),
    db: Session = Depends(get_db),
):
    """Get all observing locations."""
    query = db.query(ObservingLocation)
    if active_only:
        query = query.filter(ObservingLocation.is_active == True)
    return query.all()


@router.get("/locations/{location_id}", response_model=ObservingLocationResponse)
async def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get a specific location by ID."""
    location = db.query(ObservingLocation).filter(ObservingLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return location


@router.get("/locations/default/get", response_model=ObservingLocationResponse)
async def get_default_location(db: Session = Depends(get_db)):
    """Get the default observing location."""
    location = db.query(ObservingLocation).filter(ObservingLocation.is_default == True).first()
    if not location:
        raise HTTPException(status_code=404, detail="No default location configured")
    return location


@router.post("/locations", response_model=ObservingLocationResponse)
async def create_location(location: ObservingLocationCreate, db: Session = Depends(get_db)):
    """Create a new observing location."""
    existing = db.query(ObservingLocation).filter(ObservingLocation.name == location.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Location '{location.name}' already exists")

    # If this is set as default, unset other defaults
    if location.is_default:
        db.query(ObservingLocation).filter(ObservingLocation.is_default == True).update({"is_default": False})

    db_location = ObservingLocation(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


@router.put("/locations/{location_id}", response_model=ObservingLocationResponse)
async def update_location(location_id: int, update: ObservingLocationUpdate, db: Session = Depends(get_db)):
    """Update an observing location."""
    location = db.query(ObservingLocation).filter(ObservingLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")

    update_data = update.model_dump(exclude_unset=True)

    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(ObservingLocation).filter(ObservingLocation.is_default == True).update({"is_default": False})

    for key, value in update_data.items():
        setattr(location, key, value)

    db.commit()
    db.refresh(location)
    return location


@router.delete("/locations/{location_id}")
async def delete_location(location_id: int, db: Session = Depends(get_db)):
    """Delete an observing location."""
    location = db.query(ObservingLocation).filter(ObservingLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")

    db.delete(location)
    db.commit()
    return {"message": f"Location '{location.name}' deleted"}


# ========================================================================
# Wish List Endpoints
# ========================================================================


@router.get("/wishlist")
async def get_wishlist(db: Session = Depends(get_db)):
    """Get user's wish list of favorite targets."""
    import json

    setting = db.query(AppSetting).filter(AppSetting.key == "user.wishlist_targets").first()

    if not setting:
        return []

    try:
        wishlist = json.loads(setting.value)
        return wishlist
    except json.JSONDecodeError:
        return []


@router.put("/wishlist")
async def update_wishlist(wishlist: List[dict], db: Session = Depends(get_db)):
    """Update user's wish list of favorite targets."""
    import json

    setting = db.query(AppSetting).filter(AppSetting.key == "user.wishlist_targets").first()

    wishlist_json = json.dumps(wishlist)

    if setting:
        # Update existing
        setting.value = wishlist_json
    else:
        # Create new
        setting = AppSetting(
            key="user.wishlist_targets",
            value=wishlist_json,
            value_type="json",
            category="user",
            description="User's favorite targets wish list",
        )
        db.add(setting)

    db.commit()
    return {"message": "Wishlist updated successfully", "count": len(wishlist)}


# ========================================================================
# User Profile Settings (location + preferences as a single document)
# ========================================================================

_PREF_KEYS = {
    "temperatureUnit": "user.pref.temperature_unit",
    "distanceUnit": "user.pref.distance_unit",
    "showThumbnails": "user.pref.show_thumbnails",
    "autoRefresh": "user.pref.auto_refresh",
}

_PREF_DEFAULTS = {
    "temperatureUnit": "F",
    "distanceUnit": "mi",
    "showThumbnails": "true",
    "autoRefresh": "false",
}


class UserSettings(BaseModel):
    locationName: str = ""
    latitude: float = 40.7128
    longitude: float = -74.0060
    elevation: float = 0.0
    timezone: str = "America/New_York"
    temperatureUnit: str = "F"
    distanceUnit: str = "mi"
    showThumbnails: bool = True
    autoRefresh: bool = False


@router.get("/user", response_model=UserSettings)
async def get_user_settings(db: Session = Depends(get_db)):
    """Get user settings (default observing location + UI preferences)."""
    location = db.query(ObservingLocation).filter(ObservingLocation.is_default == True).first()

    db_keys = list(_PREF_KEYS.values())
    prefs_rows = db.query(AppSetting).filter(AppSetting.key.in_(db_keys)).all()
    prefs = {row.key: row.value for row in prefs_rows}

    def _bool(val: str) -> bool:
        return val.lower() in ("true", "1", "yes")

    return UserSettings(
        locationName=location.name if location else "",
        latitude=location.latitude if location else 40.7128,
        longitude=location.longitude if location else -74.0060,
        elevation=location.elevation if location else 0.0,
        timezone=location.timezone if location else "America/New_York",
        temperatureUnit=prefs.get(_PREF_KEYS["temperatureUnit"], _PREF_DEFAULTS["temperatureUnit"]),
        distanceUnit=prefs.get(_PREF_KEYS["distanceUnit"], _PREF_DEFAULTS["distanceUnit"]),
        showThumbnails=_bool(prefs.get(_PREF_KEYS["showThumbnails"], _PREF_DEFAULTS["showThumbnails"])),
        autoRefresh=_bool(prefs.get(_PREF_KEYS["autoRefresh"], _PREF_DEFAULTS["autoRefresh"])),
    )


@router.put("/user", response_model=UserSettings)
async def update_user_settings(settings: UserSettings, db: Session = Depends(get_db)):
    """Save user settings (upserts default observing location + UI preferences)."""
    # Upsert default observing location
    location = db.query(ObservingLocation).filter(ObservingLocation.is_default == True).first()
    if location:
        location.name = settings.locationName or location.name
        location.latitude = settings.latitude
        location.longitude = settings.longitude
        location.elevation = settings.elevation
        location.timezone = settings.timezone
    else:
        db_location = ObservingLocation(
            name=settings.locationName or "My Location",
            latitude=settings.latitude,
            longitude=settings.longitude,
            elevation=settings.elevation,
            timezone=settings.timezone,
            is_default=True,
            is_active=True,
        )
        db.add(db_location)

    # Upsert preferences
    pref_values = {
        _PREF_KEYS["temperatureUnit"]: settings.temperatureUnit,
        _PREF_KEYS["distanceUnit"]: settings.distanceUnit,
        _PREF_KEYS["showThumbnails"]: str(settings.showThumbnails).lower(),
        _PREF_KEYS["autoRefresh"]: str(settings.autoRefresh).lower(),
    }
    existing_prefs = {
        row.key: row
        for row in db.query(AppSetting).filter(AppSetting.key.in_(list(pref_values.keys()))).all()
    }
    for key, value in pref_values.items():
        if key in existing_prefs:
            existing_prefs[key].value = value
        else:
            db.add(AppSetting(key=key, value=value, value_type="string", category="user"))

    db.commit()
    return settings

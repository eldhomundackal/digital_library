"""Admin utility router — CRUD for countries, cities, languages."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.db.models.utils import City, Country, Language
from app.schemas.common import SuccessResponse
from app.schemas.utils import (
    CreateCityRequest,
    CreateCountryRequest,
    CreateLanguageRequest,
)

router = APIRouter(prefix="/admin/utils", tags=["Admin — Utils"])

_ADMIN_ROLES = ("admin", "superadmin")


@router.post("/countries")
async def create_country(
    payload: CreateCountryRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Create a new country."""
    existing = await db.execute(
        select(Country).where(Country.iso_code == payload.iso_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Country with this ISO code already exists."
        )
    country = Country(name=payload.name, iso_code=payload.iso_code)
    db.add(country)
    await db.commit()
    await db.refresh(country)
    return SuccessResponse(
        data={"country_id": str(country.uuid), "name": country.name, "iso_code": country.iso_code}
    )


@router.patch("/countries/{country_id}")
async def update_country(
    country_id: str,
    payload: CreateCountryRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update a country."""
    result = await db.execute(select(Country).where(Country.uuid == country_id))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found.")
    country.name = payload.name
    country.iso_code = payload.iso_code
    await db.commit()
    return SuccessResponse(data={"message": "Country updated."})


@router.delete("/countries/{country_id}")
async def delete_country(
    country_id: str,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-deactivate a country."""
    result = await db.execute(select(Country).where(Country.uuid == country_id))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found.")
    country.is_active = False
    await db.commit()
    return SuccessResponse(data={"message": "Country deactivated."})


@router.post("/countries/{country_id}/cities")
async def create_city(
    country_id: str,
    payload: CreateCityRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Add a city to a country."""
    country_result = await db.execute(
        select(Country).where(Country.uuid == country_id)
    )
    country = country_result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found.")
    city = City(name=payload.name, state=payload.state, country_id=country.id)
    db.add(city)
    await db.commit()
    await db.refresh(city)
    return SuccessResponse(
        data={"city_id": str(city.uuid), "name": city.name, "state": city.state}
    )


@router.patch("/cities/{city_id}")
async def update_city(
    city_id: str,
    payload: CreateCityRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update a city."""
    result = await db.execute(select(City).where(City.uuid == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")
    city.name = payload.name
    city.state = payload.state
    await db.commit()
    return SuccessResponse(data={"message": "City updated."})


@router.delete("/cities/{city_id}")
async def delete_city(
    city_id: str,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-deactivate a city."""
    result = await db.execute(select(City).where(City.uuid == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")
    city.is_active = False
    await db.commit()
    return SuccessResponse(data={"message": "City deactivated."})


@router.post("/languages")
async def create_language(
    payload: CreateLanguageRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Create a new language."""
    existing = await db.execute(
        select(Language).where(Language.iso_code == payload.iso_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Language with this ISO code already exists."
        )
    language = Language(name=payload.name, iso_code=payload.iso_code)
    db.add(language)
    await db.commit()
    await db.refresh(language)
    return SuccessResponse(
        data={"language_id": str(language.uuid), "name": language.name, "iso_code": language.iso_code}
    )


@router.patch("/languages/{language_id}")
async def update_language(
    language_id: str,
    payload: CreateLanguageRequest,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update a language."""
    result = await db.execute(select(Language).where(Language.uuid == language_id))
    language = result.scalar_one_or_none()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found.")
    language.name = payload.name
    language.iso_code = payload.iso_code
    await db.commit()
    return SuccessResponse(data={"message": "Language updated."})


@router.delete("/languages/{language_id}")
async def delete_language(
    language_id: str,
    current_user=Depends(require_roles(*_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Soft-deactivate a language."""
    result = await db.execute(select(Language).where(Language.uuid == language_id))
    language = result.scalar_one_or_none()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found.")
    language.is_active = False
    await db.commit()
    return SuccessResponse(data={"message": "Language deactivated."})

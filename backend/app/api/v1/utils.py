"""Public utility router — countries, cities, languages."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db.models.utils import City, Country, Language
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/utils", tags=["Utils"])


@router.get("/countries")
async def list_countries(db: AsyncSession = Depends(get_db)) -> SuccessResponse:
    """Return all active countries."""
    result = await db.execute(
        select(Country).where(Country.is_active.is_(True)).order_by(Country.name)
    )
    countries = result.scalars().all()
    items = [
        {"country_id": str(c.uuid), "name": c.name, "iso_code": c.iso_code}
        for c in countries
    ]
    return SuccessResponse(data=items)


@router.get("/countries/{country_id}/cities")
async def list_cities(
    country_id: str, db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """Return active cities for a specific country."""
    country_result = await db.execute(
        select(Country).where(Country.uuid == country_id, Country.is_active.is_(True))
    )
    country = country_result.scalar_one_or_none()
    if not country:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Country not found.")

    result = await db.execute(
        select(City)
        .where(City.country_id == country.id, City.is_active.is_(True))
        .order_by(City.name)
    )
    cities = result.scalars().all()
    items = [
        {"city_id": str(c.uuid), "name": c.name, "state": c.state}
        for c in cities
    ]
    return SuccessResponse(data=items)


@router.get("/languages")
async def list_languages(db: AsyncSession = Depends(get_db)) -> SuccessResponse:
    """Return all active languages."""
    result = await db.execute(
        select(Language).where(Language.is_active.is_(True)).order_by(Language.name)
    )
    languages = result.scalars().all()
    items = [
        {"language_id": str(lang.uuid), "name": lang.name, "iso_code": lang.iso_code}
        for lang in languages
    ]
    return SuccessResponse(data=items)

"""Schemas for countries, cities, languages, and publisher summary."""

from pydantic import BaseModel


class CountrySummary(BaseModel):
    """Minimal country info used in nested responses."""

    country_id: str
    name: str
    iso_code: str


class CountryResponse(BaseModel):
    """Full country detail."""

    country_id: str
    name: str
    iso_code: str
    phone_code: str | None
    flag: str | None
    is_seeded: bool


class CitySummary(BaseModel):
    """Minimal city info used in nested responses."""

    city_id: str
    name: str
    state: str | None


class CityResponse(BaseModel):
    """Full city detail."""

    city_id: str
    name: str
    state: str | None
    country: CountrySummary
    is_seeded: bool


class LanguageSummary(BaseModel):
    """Minimal language info used in nested responses."""

    language_id: str
    name: str
    iso_code: str


class CreateCountryRequest(BaseModel):
    """Body for POST /admin/utils/countries."""

    name: str
    iso_code: str
    phone_code: str | None = None
    flag: str | None = None


class CreateCityRequest(BaseModel):
    """Body for POST /admin/utils/countries/{id}/cities."""

    name: str
    state: str | None = None


class CreateLanguageRequest(BaseModel):
    """Body for POST /admin/utils/languages."""

    name: str
    iso_code: str


class PublisherSummary(BaseModel):
    """Minimal publisher info used in book and KYC responses."""

    publisher_id: str
    display_name: str
    logo: str | None
    is_verified: bool

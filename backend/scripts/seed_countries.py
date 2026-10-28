"""
Seeds countries and cities from an open dataset JSON file.

Dataset: https://github.com/dr5hn/countries-states-cities-database
Download countries+cities JSON, place at scripts/data/countries.json
Run: python scripts/seed_countries.py

Idempotent: skips existing records (matched by iso_code for countries,
name+country for cities). Safe to re-run.
"""

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.utils import City, Country


async def seed() -> None:
    """Seed countries and cities from JSON data file."""
    data_path = Path("scripts/data/countries.json")
    if not data_path.exists():
        print("ERROR: scripts/data/countries.json not found.")
        print("Download from https://github.com/dr5hn/countries-states-cities-database")
        sys.exit(1)

    data = json.loads(data_path.read_text())
    countries_seeded = 0
    cities_seeded = 0

    async with AsyncSessionLocal() as db:
        for country_data in data:
            iso_code = country_data.get("iso2", "")
            name = country_data.get("name", "")
            if not iso_code or not name:
                continue

            existing = await db.execute(
                select(Country).where(Country.iso_code == iso_code)
            )
            country = existing.scalar_one_or_none()
            if not country:
                country = Country(name=name, iso_code=iso_code)
                db.add(country)
                await db.flush()
                countries_seeded += 1

            for city_data in country_data.get("cities", []):
                city_name = city_data.get("name", "")
                state_name = city_data.get("state_name", None)
                if not city_name:
                    continue
                existing_city = await db.execute(
                    select(City).where(
                        City.name == city_name,
                        City.country_id == country.id,
                    )
                )
                if not existing_city.scalar_one_or_none():
                    db.add(
                        City(name=city_name, state=state_name, country_id=country.id)
                    )
                    cities_seeded += 1

        await db.commit()

    print(f"Seeded {countries_seeded} countries and {cities_seeded} cities.")


asyncio.run(seed())

"""
Route configuration for the airfare data-collection module.

The project maintains a list of major Indian cities.
Directional routes are generated automatically from that list.

This file defines the collection route universe.
It does NOT define statistical index weights.
"""

from itertools import permutations


# Major Indian cities used for the initial collection universe.
# The IATA code is used when querying the flight API.
MAJOR_INDIAN_CITIES: dict[str, str] = {
    "Delhi": "DEL",
    "Mumbai": "BOM",
    "Bengaluru": "BLR",
    "Chennai": "MAA",
    "Hyderabad": "HYD",
    "Kolkata": "CCU",
    "Ahmedabad": "AMD",
    "Pune": "PNQ",
    "Kochi": "COK",
    "Goa": "GOI",
}


def get_city_codes() -> list[str]:
    """Return the IATA codes of all configured cities."""
    return list(MAJOR_INDIAN_CITIES.values())


def get_all_directional_routes() -> list[tuple[str, str]]:
    """
    Generate every directional route between the configured cities.

    Both directions are included.

    Example:
        DEL -> BLR
        BLR -> DEL
    """
    return list(permutations(get_city_codes(), 2))


ALL_DIRECTIONAL_ROUTES = get_all_directional_routes()
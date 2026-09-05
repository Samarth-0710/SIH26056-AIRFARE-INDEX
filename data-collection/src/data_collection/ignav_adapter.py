import os
import time
from datetime import date, datetime
from typing import Any

import requests
from dotenv import load_dotenv

from .booking_windows import (
    SUPPORTED_BOOKING_WINDOWS,
    get_travel_date,
)
from .models import RawFareRecord
from .routes import ALL_DIRECTIONAL_ROUTES


load_dotenv()


class IgnavFareAdapter:
    """
    Adapter for collecting airfare data from Ignav.

    Collection universe:
        10 cities
        90 directional routes
        5 booking windows

    Total possible route-window searches:
        90 × 5 = 450

    Each search can return multiple flight itineraries.
    """

    BASE_URL = "https://ignav.com/api/fares/one-way"

    def __init__(
        self,
        api_key: str | None = None,
        max_retries: int = 2,
        retry_delay: int = 5,
    ):
        self.api_key = api_key or os.getenv("IGNAV_API_KEY")

        if not self.api_key:
            raise ValueError(
                "IGNAV_API_KEY is not configured."
            )

        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def search_route(
        self,
        origin: str,
        destination: str,
        travel_date: date,
    ) -> list[dict[str, Any]]:
        """
        Search Ignav for one route and travel date.

        Temporary API failures are retried before the
        request is considered unsuccessful.
        """

        payload = {
            "origin": origin,
            "destination": destination,
            "departure_date": travel_date.isoformat(),
            "market": "IN",
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.BASE_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=30,
                )

                response.raise_for_status()

                data = response.json()

                return data.get("itineraries", [])

            except requests.RequestException as error:

                if attempt >= self.max_retries:
                    print(
                        f"FAILED: {origin} -> {destination} | "
                        f"{travel_date} | {error}"
                    )
                    return []

                print(
                    f"Retry {attempt + 1}/{self.max_retries} "
                    f"for {origin} -> {destination} | "
                    f"{travel_date}"
                )

                time.sleep(self.retry_delay)

        return []

    def collect_route_window(
        self,
        origin: str,
        destination: str,
        observation_date: date,
        booking_window: int,
    ) -> list[RawFareRecord]:
        """
        Collect all returned itineraries for one route
        and one booking window.
        """

        travel_date = get_travel_date(
            observation_date,
            booking_window,
        )

        itineraries = self.search_route(
            origin=origin,
            destination=destination,
            travel_date=travel_date,
        )

        records: list[RawFareRecord] = []

        observation_timestamp = datetime.now()

        for itinerary in itineraries:
            record = self._convert_to_raw_record(
                itinerary=itinerary,
                origin=origin,
                destination=destination,
                travel_date=travel_date,
                observation_date=observation_date,
                booking_window=booking_window,
                observation_timestamp=observation_timestamp,
            )

            if record is not None:
                records.append(record)

        return records

    def collect_all(
        self,
        observation_date: date | None = None,
    ) -> list[RawFareRecord]:
        """
        Collect all configured routes across all
        supported booking windows.

        90 routes × 5 booking windows = 450 searches.

        Failed route/window searches are skipped after
        retries so that one API failure does not stop
        the complete collection process.
        """

        if observation_date is None:
            observation_date = date.today()

        records: list[RawFareRecord] = []

        total_searches = (
            len(ALL_DIRECTIONAL_ROUTES)
            * len(SUPPORTED_BOOKING_WINDOWS)
        )

        completed_searches = 0

        print("\nStarting full collection:")
        print(
            f"{len(ALL_DIRECTIONAL_ROUTES)} routes × "
            f"{len(SUPPORTED_BOOKING_WINDOWS)} booking windows "
            f"= {total_searches} searches\n"
        )

        for origin, destination in ALL_DIRECTIONAL_ROUTES:

            for booking_window in SUPPORTED_BOOKING_WINDOWS:

                completed_searches += 1

                print(
                    f"[{completed_searches}/{total_searches}] "
                    f"{origin} -> {destination} | "
                    f"T+{booking_window}"
                )

                route_records = self.collect_route_window(
                    origin=origin,
                    destination=destination,
                    observation_date=observation_date,
                    booking_window=booking_window,
                )

                records.extend(route_records)

                print(
                    f"    Records collected: "
                    f"{len(route_records)}"
                )

        print("\nCollection complete.")
        print(
            f"Total raw records: {len(records)}"
        )

        return records

    @staticmethod
    def _convert_to_raw_record(
        itinerary: dict[str, Any],
        origin: str,
        destination: str,
        travel_date: date,
        observation_date: date,
        booking_window: int,
        observation_timestamp: datetime,
    ) -> RawFareRecord | None:
        """
        Convert one Ignav itinerary into RawFareRecord.
        """

        outbound = itinerary.get("outbound", {})

        segments = outbound.get("segments", [])

        if not segments:
            return None

        first_segment = segments[0]

        # Price
        price = itinerary.get("price", {})

        fare_amount = price.get("amount")
        currency = price.get("currency", "INR")

        if fare_amount is None:
            return None

        # Departure time
        departure_time_raw = first_segment.get(
            "departure_time_local"
        )

        if not departure_time_raw:
            return None

        try:
            departure_time = datetime.fromisoformat(
                departure_time_raw
            ).time()
        except ValueError:
            return None

        # Airline
        airline = outbound.get(
            "carrier",
            first_segment.get(
                "operating_carrier_name",
                "UNKNOWN",
            ),
        )

        # Flight number
        flight_number = first_segment.get(
            "flight_number",
            "UNKNOWN",
        )

        # Cabin class
        cabin_class = itinerary.get(
            "cabin_class",
            "UNKNOWN",
        )

        # Baggage
        baggage = itinerary.get(
            "bags",
            {},
        )

        baggage_characteristics = (
            str(baggage)
            if baggage
            else "NOT_SPECIFIED"
        )

        return RawFareRecord(
            origin=origin,
            destination=destination,
            travel_date=travel_date,
            observation_date=observation_date,
            booking_window=booking_window,
            airline=airline,
            flight_number=flight_number,
            departure_time=departure_time,
            cabin_class=cabin_class.upper(),

            # Ignav does not currently provide a reliable
            # fare-type field in the response we mapped.
            fare_type="UNKNOWN",

            baggage_characteristics=baggage_characteristics,
            fare_amount=float(fare_amount),
            currency=currency,
            source="ignav",
            observation_timestamp=observation_timestamp,

            metadata={
                "ignav_id": itinerary.get(
                    "ignav_id"
                ),
                "price_status": price.get(
                    "status"
                ),
                "requires_self_transfer": itinerary.get(
                    "requires_self_transfer",
                    False,
                ),
                "duration_minutes": outbound.get(
                    "duration_minutes"
                ),
                "marketing_carrier_code": first_segment.get(
                    "marketing_carrier_code"
                ),
                "operating_carrier_name": first_segment.get(
                    "operating_carrier_name"
                ),
                "departure_timezone": first_segment.get(
                    "departure_timezone"
                ),
                "arrival_airport": first_segment.get(
                    "arrival_airport"
                ),
                "arrival_time_local": first_segment.get(
                    "arrival_time_local"
                ),
                "aircraft": first_segment.get(
                    "aircraft"
                ),
            },
        )
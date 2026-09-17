import os
import time
from datetime import date, datetime, timedelta
from typing import Any

import requests
from dotenv import load_dotenv

from .adapters import SourceStatus
from .booking_windows import (
    SUPPORTED_BOOKING_WINDOWS,
    get_travel_date,
)
from .models import RawFareRecord
from .routes import ALL_DIRECTIONAL_ROUTES


from pathlib import Path


def _load_env_config() -> None:
    load_dotenv()
    if not os.getenv("IGNAV_API_KEY"):
        candidates = [
            Path("backend/.env"),
            Path(__file__).resolve().parents[3] / "backend" / ".env",
            Path(__file__).resolve().parents[2] / "backend" / ".env",
            Path("../backend/.env"),
        ]
        for c in candidates:
            if c.exists():
                load_dotenv(dotenv_path=c)
                if os.getenv("IGNAV_API_KEY"):
                    break


_load_env_config()


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
        if api_key is None:
            if not os.getenv("IGNAV_API_KEY"):
                _load_env_config()
            self.api_key = os.getenv("IGNAV_API_KEY")
        else:
            self.api_key = api_key
        self.headers = {
            "X-Api-Key": self.api_key or "",
            "Content-Type": "application/json",
        }
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._cached_connection_status: tuple[SourceStatus, str, float] | None = None

    def get_status(self) -> SourceStatus:
        if not self.api_key:
            return SourceStatus.UNAVAILABLE
        if self._cached_connection_status:
            return self._cached_connection_status[0]
        return SourceStatus.AVAILABLE

    def check_connection(
        self,
        force_check: bool = False,
        timeout: float = 6.0,
    ) -> tuple[SourceStatus, str]:
        """Verify real runtime connectivity to the Ignav live API.

        Checks:
        1. Whether IGNAV_API_KEY is present server-side.
        2. Dispatches a live probe request to the Ignav API.
        3. Caches successful/error status for 60 seconds to prevent rate-limiting.

        Returns:
            (SourceStatus, message_string)
        """
        if not self.api_key:
            return (
                SourceStatus.UNAVAILABLE,
                "Live API credentials unconfigured; fallback active",
            )

        now = time.time()
        if not force_check and self._cached_connection_status is not None:
            cached_status, cached_msg, cached_time = self._cached_connection_status
            if now - cached_time < 60.0:
                return (cached_status, cached_msg)

        probe_date = date.today() + timedelta(days=15)
        payload = {
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": probe_date.isoformat(),
            "market": "IN",
        }

        try:
            resp = requests.post(
                self.BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=timeout,
            )
            if resp.status_code == 200:
                status = SourceStatus.AVAILABLE
                message = "Live Ignav airfare data is available."
            elif resp.status_code in (401, 403):
                status = SourceStatus.UNAVAILABLE
                message = "Ignav API authentication failed; credentials invalid."
            elif resp.status_code == 429:
                status = SourceStatus.DEGRADED
                message = "Ignav API rate limit reached; synthetic fallback active."
            else:
                status = SourceStatus.DEGRADED
                message = f"Ignav API returned status {resp.status_code}; synthetic fallback active."
        except requests.exceptions.Timeout:
            status = SourceStatus.DEGRADED
            message = "Ignav API request timed out; synthetic fallback active."
        except requests.exceptions.RequestException as exc:
            status = SourceStatus.DEGRADED
            message = f"Live Ignav API unreachable ({type(exc).__name__}); synthetic fallback active."
        except Exception as exc:
            status = SourceStatus.DEGRADED
            message = f"Ignav live connection error: {str(exc)}"

        self._cached_connection_status = (status, message, now)
        return (status, message)

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
        if not self.api_key:
            raise ValueError(
                "IGNAV_API_KEY is not configured. Set the IGNAV_API_KEY environment variable or pass api_key to query Ignav."
            )


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
        observation_date: date | None = None,
        booking_window: int = 15,
    ) -> list[RawFareRecord]:
        """
        Collect all returned itineraries for one route
        and one booking window.
        """
        if observation_date is None:
            observation_date = date.today()

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
        routes: list[tuple[str, str]] | None = None,
        booking_windows: list[int] | None = None,
    ) -> list[RawFareRecord]:
        """
        Collect all configured routes across all
        supported booking windows.

        90 routes × 5 booking windows = 450 searches by default.
        Pass `routes` to restrict collection to a specific subset.

        Failed route/window searches are skipped after
        retries so that one API failure does not stop
        the complete collection process.
        """

        if observation_date is None:
            observation_date = date.today()

        target_routes = routes if routes is not None else ALL_DIRECTIONAL_ROUTES
        target_windows = booking_windows if booking_windows is not None else SUPPORTED_BOOKING_WINDOWS

        records: list[RawFareRecord] = []

        total_searches = (
            len(target_routes)
            * len(target_windows)
        )

        completed_searches = 0

        print("\nStarting collection:")
        print(
            f"{len(target_routes)} routes × "
            f"{len(target_windows)} booking windows "
            f"= {total_searches} searches\n"
        )

        for origin, destination in target_routes:

            for booking_window in target_windows:

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
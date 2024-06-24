import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Any, Dict, List, Literal, Optional, Union

from .logger import get_logger
from .utils import get_search_bbox

from .models import (
    Coordinate,
    ViewBox,
    WazeGeocodeParams,
    WazeLocation,
    WazeRequestBody,
    WazeReview,
    WazeTravelPlan,
    WazeVenue,
)

from .cfg import (
    BASE_URL,
    DEFAULT_HEADERS,
    GEOCODE_EXT,
    PLANNER_EXT,
    REVIEWS_EXT,
    VENUES_EXT,
    Countries,
)


class WazeHTTPError(Exception):
    pass


class Waze(requests.Session):
    def __init__(
        self,
        locale: Optional[Union[Coordinate, Countries]] = None,
        log_level: Optional[Literal["normal", "verbose", "quiet"]] = "normal",
        _base_url: str = BASE_URL,
        _planner_ext: str = PLANNER_EXT,
        _geocode_ext: str = GEOCODE_EXT,
        _venues_ext: str = VENUES_EXT,
        _reviews_ext: str = REVIEWS_EXT,
        _headers: Dict[str, Any] = DEFAULT_HEADERS,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
        **session_kwargs,
    ):
        super().__init__(**session_kwargs)
        self.locale = locale
        self.logger = get_logger(log_level)
        self._base_url = _base_url
        self._planner_ext = _planner_ext
        self._geocode_ext = _geocode_ext
        self._venues_ext = _venues_ext
        self._reviews_ext = _reviews_ext
        self._headers = _headers

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("https://", adapter)
        self.mount("http://", adapter)

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        try:
            response = self.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise WazeHTTPError(f"HTTP request failed: {e}") from e

    def _infer_locale(self) -> None:
        if not self.locale:
            raise ValueError("No locale specified, cannot geocode without a locale.")
        elif isinstance(self.locale, Coordinate):
            pass
        elif isinstance(self.locale, Countries):
            self.locale = self.locale.value
            self.logger.info(f"Locale set to {self.locale}")
        else:
            raise TypeError("Unknown value passed in for `locale`")

    def _prepare_geocode_params(
        self, query: str, viewbox: ViewBox
    ) -> WazeGeocodeParams:
        return {
            "q": query,
            "v": f"{viewbox.lat1},{viewbox.long1};{viewbox.lat2},{viewbox.long2}",
            "exp": "8,10,12",
            "geo-env": "row",
            "lang": "en",
        }

    def geocode(self, query: str, radius: int = 100) -> List[WazeLocation]:
        self._infer_locale()
        params = self._prepare_geocode_params(
            query=query, viewbox=get_search_bbox(self.locale, radius)
        )
        self.logger.info(
            f"[geocode] Making request with the following parameters:\n{params}"
        )

        response = self._make_request(
            "GET", self._base_url + self._geocode_ext, params=params
        )
        return [WazeLocation(**o) for o in response.json()]

    def venue(self, location: Union[WazeLocation, str]) -> WazeVenue:
        venue_id = (
            location.venueId.replace("venues.", "").replace("googlePlaces.", "")
            if isinstance(location, WazeLocation)
            else location
        )
        response = self._make_request(
            "GET", f"{self._base_url}{self._venues_ext}/{venue_id}"
        )
        return WazeVenue(**response.json())

    def reviews(self, venue: WazeVenue) -> List[WazeReview]:
        try:
            response = self._make_request(
                "GET", f"{self._base_url}{self._reviews_ext}/{venue.googlePlaceId}"
            )
            return WazeReview(**response.json())
        except WazeHTTPError as e:
            if "500" in str(e):
                self.logger.info("No reviews found for this venue.")
                return []
            raise

    def plan(self, src: Coordinate, dst: Coordinate) -> WazeTravelPlan:
        params = WazeRequestBody(from_=src, to=dst)
        self.logger.info(
            f"[plan] Making request with the following parameters:\n{params.model_dump(by_alias=True)}"
        )

        response = self._make_request(
            "POST",
            self._base_url + self._planner_ext,
            headers=self._headers,
            json=params.model_dump(by_alias=True),
        )

        resp_json = response.json()
        alternatives = resp_json.get("alternatives")
        if not alternatives:
            raise ValueError(f"Response is empty:\n{resp_json}")

        assert len(alternatives) == params.nPaths, "Only get the fastest route (1)"
        route = alternatives[0]
        plan = route.get("response")
        if not plan:
            raise ValueError(f"Plan is empty:\n{alternatives}")

        geo_path = [Coordinate(**o) for o in route.get("coords")]

        return WazeTravelPlan(src=src, dst=dst, geoPath=geo_path, **plan)

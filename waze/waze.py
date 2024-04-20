import requests
from typing import Any, Dict, List, Literal, Optional, Union

from .logger import get_logger
from .utils import get_feasible_search_area

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
    ARBITRARY_HEADERS,
    GEOCODE_EXT,
    PLANNER_EXT,
    REVIEWS_EXT,
    VENUES_EXT,
    Countries,
)


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
        _headers: Dict[str, Any] = ARBITRARY_HEADERS,
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
            "v": f"{viewbox.x1},{viewbox.y1};{viewbox.x2},{viewbox.y2}",
            "exp": "8,10,12",
            "lang": "en",
        }

    def geocode(self, query: str, radius: int = 1_000) -> List[WazeLocation]:
        # if no locale specified, raise error
        # cannot geocode without a proximate locality
        if not self.locale or isinstance(self.locale, Countries):
            self._infer_locale()

        params = self._prepare_geocode_params(
            query=query, viewbox=get_feasible_search_area(self.locale, radius)
        )

        self.logger.info(
            f"[geocode] Making request with the following parameters:\n{params}"
        )

        resp = self.get(url=self._base_url + self._geocode_ext, params=params)
        if not resp.ok:
            raise requests.HTTPError(f"Server returned {resp.status_code}\n{resp.text}")

        resp = resp.json()
        return [WazeLocation(**o) for o in resp]

    def venue(self, location: Union[WazeLocation, str]) -> WazeVenue:
        resp = self.get(
            url=self._base_url
            + self._venues_ext
            + f"/{location.venueId.replace('venues.', '')}"
        )

        if not resp.ok:
            raise requests.HTTPError(f"Server returned {resp.status_code}\n{resp.text}")

        resp = resp.json()
        return WazeVenue(**resp)

    def reviews(self, venue: WazeVenue) -> List[WazeReview]:
        resp = self.get(
            url=self._base_url + self._reviews_ext + f"/{venue.googlePlaceId}"
        )

        if not resp.ok:
            # in this case there aren't any reviews
            if resp.status_code == 500:
                return []
            raise requests.HTTPError(f"Server returned {resp.status_code}\n{resp.text}")

        resp = resp.json()
        return WazeReview(**resp)

    def plan(self, src: Coordinate, dst: Coordinate) -> WazeTravelPlan:
        # make the POST request
        params = WazeRequestBody(from_=src, to=dst)  # type: ignore
        self.logger.info(
            f"[plan] Making request with the following parameters:\n"
            f"{params.model_dump(by_alias=True)}"
        )

        resp = self.post(
            url=self._base_url + self._planner_ext,
            headers=self._headers,
            json=params.model_dump(by_alias=True),
        )

        # parsing the response
        if not resp.ok:
            raise requests.HTTPError(f"Server returned {resp.status_code}\n{resp.text}")

        resp = resp.json()
        alternatives = resp.get("alternatives")
        if not alternatives:
            raise ValueError(f"Response is empty:\n{resp}")

        assert len(alternatives) == params.nPaths, "Only get the fastest route (1)"
        route = alternatives[0]
        plan = route.get("response")
        if not plan:
            raise ValueError(f"Plan is empty:\n{alternatives}")

        geo_path = [Coordinate(**o) for o in route.get("coords")]

        return WazeTravelPlan(src=src, dst=dst, geoPath=geo_path, **plan)

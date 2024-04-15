import math
import requests
from typing import List, Optional
from json import JSONDecodeError
from pydantic import AliasChoices, BaseModel, Field


class Coordinate(BaseModel):
    name: Optional[str] = Field(default=None)
    latitude: float = Field(
        ..., validation_alias=AliasChoices("y", "latitude"), serialization_alias="y"
    )
    longitude: float = Field(
        ..., validation_alias=AliasChoices("x", "longitude"), serialization_alias="x"
    )


class WazeRequestBody(BaseModel):
    from_: Coordinate = Field(..., alias="from")
    to: Coordinate = Field(...)
    nPaths: int = Field(default=1)
    useCase: str = Field(default="LIVEMAP_PLANNING")
    interval: int = Field(default=100)
    arriveAt: bool = Field(default=True)

    class Config:
        populate_by_name = True


class TollPriceItem(BaseModel):
    tollPrice: float


class ETAHistogramItem(BaseModel):
    eta: int  # unix timestamp
    routeLengthInMinutes: int
    text: str


class WazeTravelPlan(BaseModel):
    src: Coordinate
    dst: Coordinate
    routeName: str
    geoPath: List[Coordinate]
    totalSeconds: int  # estimated journey time in seconds
    totalLength: int  # distance in meters
    isToll: bool
    tollPriceInfo: TollPriceItem
    etaHistograms: List[ETAHistogramItem]


API_URL = "https://www.waze.com/live-map/api/user-drive?geo_env=row"

# spoofing the User-Agent here, but I'm not sure if needed
ARBITRARY_HEADERS = {
    "Accept": "/_/",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": "https://www.waze.com",
    "Referer": "https://www.waze.com/live-map/directions?from="
    "place.w.68091917.680722562.2874558",
    "Sec-Ch-Ua": '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36 "
    "Edg/123.0.0.0",
}


def get_route_plan(src: Coordinate, dst: Coordinate) -> WazeTravelPlan:
    # make the POST request
    params = WazeRequestBody(from_=src, to=dst)

    response = requests.post(
        url=API_URL,
        headers=ARBITRARY_HEADERS,
        json=params.model_dump(by_alias=True),
    )

    # parsing the response
    if not response.ok:
        raise ValueError(f"API request failed:\n{response.status_code}")
    try:
        r = response.json()
    except JSONDecodeError as exc:
        raise ValueError(f"Response does not parse:\n {exc}\n{r.text}")

    r_list = r.get("alternatives")
    if not r_list:
        raise ValueError(f"Response is empty:\n{r}")

    assert len(r_list) == params.nPaths, "Only get the fastest route (1)"
    route = r_list[0]
    plan = route.get("response")
    if not plan:
        raise ValueError(f"Plan is empty:\n{r_list}")

    geo_path = [Coordinate(**o) for o in route.get("coords")]

    return WazeTravelPlan(src=src, dst=dst, geoPath=geo_path, **plan)


if __name__ == "__main__":

    """put your scheduled stuff here"""

    # SG
    star_vista = Coordinate(latitude=1.3068, longitude=103.7884)
    tuas = Coordinate(latitude=1.336450, longitude=103.647072)

    # MY
    kajang = Coordinate(latitude=2.993518, longitude=101.787407)
    georgetown = Coordinate(latitude=5.416393, longitude=100.332680)
    subang_parade = Coordinate(latitude=3.0815, longitude=101.5851)

    plan = get_route_plan(src=star_vista, dst=subang_parade)
    hr = plan.totalSeconds / 60 / 60
    distance = plan.totalLength / 1000

    print(f"{distance} km")
    print(f"{math.floor(hr)} hours and {hr % math.floor(hr) * 60:.0f} minutes")

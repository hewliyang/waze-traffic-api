from typing import List, Optional, TypedDict
from pydantic import AliasChoices, BaseModel, Field


class Coordinate(BaseModel):
    name: Optional[str] = Field(default=None)
    latitude: float = Field(
        ...,
        validation_alias=AliasChoices("y", "latitude", "lat"),
        serialization_alias="y",
    )
    longitude: float = Field(
        ...,
        validation_alias=AliasChoices("x", "longitude", "lng", "lon"),
        serialization_alias="x",
    )


class WazeGeocodeParams(TypedDict):
    q: str
    exp: str
    v: str
    lang: str


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


class Alert(BaseModel):
    id: int
    type: str
    subtype: str
    location: Coordinate


class WazeTravelPlan(BaseModel):
    src: Coordinate
    dst: Coordinate
    routeName: str
    geoPath: List[Coordinate]
    alerts: List[Alert]
    totalSeconds: int  # estimated journey time in seconds
    totalLength: int  # distance in meters
    isToll: bool
    isFastest: bool
    tollPriceInfo: TollPriceItem
    etaHistograms: Optional[List[ETAHistogramItem]] = None


class ViewBox(BaseModel):
    long1: float
    lat1: float
    long2: float
    lat2: float


class WazeLocation(BaseModel):
    address: str
    cleanName: str
    latLng: Coordinate
    name: str
    venueId: str


class WazeVenueAddress(BaseModel):
    countryCode: Optional[str] = None
    countryName: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    cityId: Optional[int] = None
    street: Optional[str] = None
    streetId: Optional[int] = None
    segmentId: Optional[int] = None
    houseNumber: Optional[int] = None


class WazeVenueLink(BaseModel):
    href: str
    text: str


class ImageType(BaseModel):
    small: str
    large: str


class WazeVenueImage(BaseModel):
    id: str
    src: ImageType


class TimeUnit(BaseModel):
    hours: int
    minutes: int


class WazeVenueHours(BaseModel):
    day: int
    from_: TimeUnit = Field(..., alias="from")
    to: TimeUnit

    class Config:
        populate_by_name = True


class WazeVenue(BaseModel):
    geoEnv: Optional[str] = None
    latLng: Optional[Coordinate] = None
    id: Optional[str] = None
    address: Optional[WazeVenueAddress] = None
    name: Optional[str] = None
    phone: Optional[WazeVenueLink] = None
    url: Optional[WazeVenueLink] = None
    services: Optional[List[str]] = None
    lastUpdateDate: Optional[int] = None  # unix timestamp
    creationDate: Optional[int] = None  # unix timestamp
    images: Optional[List[WazeVenueImage]] = None
    hours: Optional[List[WazeVenueHours]] = None
    googlePlaceId: Optional[str] = None
    alternativeName: Optional[str] = None


class Review(BaseModel):
    author_name: str
    author_url: str
    profile_photo_url: str
    rating: int
    relative_time_description: str
    text: str
    time: int  # unix timestamp


class Ratings(BaseModel):
    average: float
    counts: List[int]  # idk what this is


class WazeReview(BaseModel):
    reviews: List[Review]
    ratings: Ratings

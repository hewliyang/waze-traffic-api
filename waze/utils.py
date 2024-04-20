from math import cos, radians
from functools import partial
from .models import ViewBox, Coordinate

round_to_7_dp = partial(round, ndigits=7)


def get_feasible_search_area(point: Coordinate, radius: int = 1_000) -> ViewBox:
    """Computes a rectangular feasible search area around
    user locale of `radius` kilometers.

    Args:
        point (Coordinate):
                User locale
        radius (int, optional):
                Radius of desired viewport based on user locale.
                Defaults to 300.

    Returns:
        ViewBox: Object containing bounding box coords
    """

    EARTH_RADIUS = 6371
    lat_delta = radius / EARTH_RADIUS
    lon_delta = radius / (EARTH_RADIUS * cos(radians(point.latitude)))

    return ViewBox(
        x1=round_to_7_dp(point.latitude - lat_delta),
        y1=round_to_7_dp(point.longitude - lon_delta),
        x2=round_to_7_dp(point.latitude + lat_delta),
        y2=round_to_7_dp(point.longitude + lon_delta),
    )

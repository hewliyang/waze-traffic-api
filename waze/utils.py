import math
from functools import partial
from .models import ViewBox, Coordinate

sevendp = partial(round, ndigits=7)


def get_search_bbox(point: Coordinate, radius: int = 100) -> ViewBox:
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

    EARTH_RADIUS_KM = 6371.0
    radius_radians = radius / EARTH_RADIUS_KM
    lat_radians = math.radians(point.latitude)
    lon_radians = math.radians(point.longitude)
    min_lat = lat_radians - radius_radians
    max_lat = lat_radians + radius_radians
    min_lon = lon_radians - radius_radians / math.cos(lat_radians)
    max_lon = lon_radians + radius_radians / math.cos(lat_radians)

    return ViewBox(
        long1=sevendp(math.degrees(min_lon)),
        lat1=sevendp(math.degrees(min_lat)),
        long2=sevendp(math.degrees(max_lon)),
        lat2=sevendp(math.degrees(max_lat)),
    )

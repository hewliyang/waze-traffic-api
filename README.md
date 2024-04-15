# waze-traffic-api

Query the public facing Waze traffic API as a free alternative to Google's Distance Matrix API. I'm also pretty sure that its the same endpoint used in-app.

To use, install `requests` and `pydantic`. For the [notebook](waze.ipynb) you will additional need `geopandas`, `matplotlib` and `ipykernel`. Alternatively, do:

```bash
# use a virtualenv if you'd like
virtualenv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Usage

Drop `waze.py` in your project or just copy paste the source code - it's only about 100 lines long.

```python
from waze import Coordinate, get_route_plan

# define your start and end points. names are optional
star_vista = Coordinate(name="Star Vista", latitude=1.3068, longitude=103.7884)
subang_parade = Coordinate(name="Subang Parade", latitude=3.0815, longitude=101.5851)

# make the request
plan = get_route_plan(src=star_vista, dst=subang_parade)

hr = plan.totalSeconds / 60 / 60
distance = plan.totalLength / 1000

print(f"Route: {plan.src.name} => {plan.dst.name} , {plan.routeName}")
print(f"Distance: {distance} km")
print(f"Estimated Travel Time: {int(hr)} hours and {hr % int(hr) * 60:.0f} minutes")
print(f"Toll : {plan.isToll}")
print(f"Toll Price : RM{plan.tollPriceInfo.tollPrice}")


"""
Output:

Route: Star Vista => Subang Parade , E2 Lebuhraya Utara Selatan Simpang Renggam
Distance: 368.63 km
Estimated Travel Time: 4 hours and 31 minutes
Toll : True
Toll Price : RM44.59
"""
```

> **Note**: I've only tested for Singapore/Malaysia at the moment so YMMV / modify as needed

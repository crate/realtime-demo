"""
This script processes a report from the EU Copernicus Climate Data Store.

Processing consists of:
1. Generating and downloading a given report
2. Converting the NetCDF file to JSON
"""
from typing import Any, Dict, List
import cdsapi
import numpy as np
import xarray as xr

# The name of the file to store the report
FILE_NAME: str = "download.nc"
# The name of the variable we are interested in to extract from the report.
# t2m stands for temperature 2 meters above the ground.
VARIABLE_NAME: str = "t2m"


def download_file(dataset: str, request: Dict[Any, Any]) -> None:
    "Downloads and saves the requested dataset"
    client = cdsapi.Client()
    client.retrieve(dataset, request, FILE_NAME)


def to_json() -> List[Dict]:
    "Parses the NetCDF file and converts it to a JSON document"
    xrds = xr.open_dataset(FILE_NAME)

    df = xrds.data_vars[VARIABLE_NAME].to_dataframe()

    result = []
    for _, row in df.iterrows():
        value = row[VARIABLE_NAME].item()
        # Some measurements don't have a value, we skip those
        if np.isnan(value):
            continue

        result.append(
            {
                "timestamp": row.name[0].value,
                "temperature": value,
                "latitude": row.name[1],
                "longitude": row.name[2],
            }
        )

    return result


def main() -> None:
    "Main method to initiate the download and parsing"

    dataset = "derived-era5-land-daily-statistics"
    request = {
        "variable": ["2m_temperature"],
        "year": "2025",
        "month": "09",
        "day": ["01"],
        "daily_statistic": "daily_mean",
        "time_zone": "utc+00:00",
        "frequency": "1_hourly",
        "data_format": "netcdf",
        "download_format": "unarchived",
    }

    download_file(dataset, request)
    # TODO This is ignoring the returned data. In the next steps,
    # data needs to be written into a message queue
    to_json()


if __name__ == "__main__":
    main()

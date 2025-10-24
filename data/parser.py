"""
This class downloads a report from the EU Copernicus Climate Data Store
and converts it to JSON documents.
"""

from typing import Dict, List
import cdsapi
import numpy as np
import xarray as xr
from data.geo import PointTester


class Parser:
    "Parses a NetCDF file"

    def __init__(
        self,
        country_iso3: str = "DEU",
    ):
        # The name of the file to store the report
        self.file_name: str = "download.nc"

        # The name of the variable we are interested in to extract from the report.
        # t2m stands for temperature 2 meters above the ground.
        self.variable_name: str = "t2m"

        # https://cds.climate.copernicus.eu/datasets/derived-era5-land-daily-statistics?tab=overview
        self.dataset = "derived-era5-land-daily-statistics"
        self.request = {
            "variable": ["2m_temperature"],
            "daily_statistic": "daily_mean",
            "time_zone": "utc+00:00",
            "frequency": "1_hourly",
            "data_format": "netcdf",
            "download_format": "unarchived",
        }

        # Load geo bounds
        self.geo = PointTester("geo/ne_110m_admin_0_countries.shp", country_iso3)

    def download_file(
        self,
        year: int = 2025,
        month: str = "09",
        day: List[str] = ["01"],
    ) -> None:
        "Downloads and saves the requested dataset"
        client = cdsapi.Client()

        client.retrieve(
            self.dataset,
            self.request | {"year": year, "month": month, "day": day},
            self.file_name,
        )

    def to_json(self) -> List[Dict]:
        "Parses the NetCDF file and converts it to a JSON document"
        xrds = xr.open_dataset(self.file_name)

        df = xrds.data_vars[self.variable_name].to_dataframe()

        # So we can only get points within desired country
        tester = PointTester("geo/ne_110m_admin_0_countries.shp")

        result = []
        for _, row in df.iterrows():
            value = row[self.variable_name].item()
            # Some measurements don't have a value, we skip those
            if np.isnan(value):
                continue

            # Within desired country?
            if self.geo.contains_latlon(float(row.name[1]), float(row.name[2])):
                result.append(
                    {
                        "timestamp": row.name[0].value,
                        "temperature": value,
                        "latitude": row.name[1],
                        "longitude": row.name[2],
                    }
                )

        return result

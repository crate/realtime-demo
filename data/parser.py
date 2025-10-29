"""
This class downloads a report from the EU Copernicus Climate Data Store
and converts it to JSON documents.
"""

from collections import defaultdict
from typing import Any, Dict, List
import logging
import zipfile
import cdsapi
import numpy as np
import xarray as xr
from geo import PointTester


class Parser:
    "Parses a NetCDF file"

    def __init__(
        self,
        country_iso3: str = "DEU",
    ):
        # Load geo bounds
        self.geo = PointTester("geo/ne_110m_admin_0_countries.shp", country_iso3)

        # The name of the file to store the report
        self.file_name: str = "download.zip"

        # https://cds.climate.copernicus.eu/datasets/derived-era5-land-daily-statistics?tab=overview
        self.dataset = "derived-era5-land-daily-statistics"
        # request_variable_name: The name of the metric as passed in the CDS API call
        # cdf_variable_name: The name of the metric (variable) inside the NetCDF file
        # payload_field_name: The name of the field as we want it to be returned from the parser
        self.variables = [
            {
                "request_variable_name": "2m_temperature",
                "cdf_variable_name": "t2m",
                "payload_field_name": "temperature",
            },
            {
                "request_variable_name": "10m_u_component_of_wind",
                "cdf_variable_name": "u10",
                "payload_field_name": "u10",
            },
            {
                "request_variable_name": "10m_v_component_of_wind",
                "cdf_variable_name": "v10",
                "payload_field_name": "v10",
            },
            {
                "request_variable_name": "surface_pressure",
                "cdf_variable_name": "sp",
                "payload_field_name": "pressure",
            },
        ]
        self.request = {
            "variable": list(map(lambda m: m["request_variable_name"], self.variables)),
            "daily_statistic": "daily_mean",
            "time_zone": "utc+00:00",
            "frequency": "1_hourly",
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": self.geo.bounds(),
        }

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

        # It contains at least one .nc file inside as it's a zip
        if zipfile.is_zipfile(self.file_name):
            with zipfile.ZipFile(self.file_name) as zf:
                zf.extractall()

    # variable_name = The name of the variable we are interested in to extract from the report.
    # t2m stands for temperature 2 meters above the ground.
    def to_json(
        self, nc_filename: str, variable_name: str, field_name: str
    ) -> List[Dict[str, Any]]:
        "Returns a list of JSON documents for a single variable"
        xrds = xr.open_dataset(nc_filename)

        df = xrds.data_vars[variable_name].to_dataframe()
        logging.info(
            "There are %s data points for the variable %s", df.size, variable_name
        )

        result = []
        for _, row in df.iterrows():
            value = row[variable_name].item()
            # Some measurements don't have a value, we skip those
            if np.isnan(value):
                continue

            # Within desired country?
            if self.geo.contains_latlon(float(row.name[1]), float(row.name[2])):
                result.append(
                    {
                        "timestamp": row.name[0].value,
                        "latitude": row.name[1],
                        "longitude": row.name[2],
                        field_name: value,
                    }
                )

        logging.info("There are %s matching data points", len(result))
        return result

    def merge_json_documents(
        self, *lists: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple lists of JSON documents (from different NetCDF variables)
        by shared timestamp, latitude, and longitude.
        """
        merged = defaultdict(dict)

        for docs in lists:
            for doc in docs:
                key = (doc["timestamp"], doc["latitude"], doc["longitude"])
                merged[key].update(doc)

        # Flatten dict-of-dicts back into a list
        return list(merged.values())

    def to_json_combined(self):
        "Returns a list of JSON documents combined for all single variables"
        results = []
        for variable in self.variables:
            single_variable_json = self.to_json(
                f"{variable['request_variable_name']}_0_{self.request['daily_statistic'].replace('_', '-')}.nc",
                variable["cdf_variable_name"],
                variable["payload_field_name"],
            )
            logging.info(
                "Found %s %s JSON documents to ingest",
                len(single_variable_json),
                variable["cdf_variable_name"],
            )
            results.append(single_variable_json)

        # Now combine all into a single set of data
        return self.merge_json_documents(*results)

# Real-Time Demo

A demo of CrateDB's real-time analytics capabilities.

## Data Generation

We use publicly available data from the [Climate Data Store](https://cds.climate.copernicus.eu/). The [ERA5-Land](https://cds.climate.copernicus.eu/datasets/derived-era5-land-daily-statistics?tab=overview) data set includes atmospheric variables, such as air temperature and air humidity from around the globe.

[data/parser.py](data/parser.py) generates a report for a given date range, parses the retrieved NetCDF file, and converts it to JSON documents. Below is an example of the final JSON document.

```json
{
    "timestamp": 1756684800000000000,
    "temperature": 295.6215515136719,
    "latitude": 40.90000000000115,
    "longitude": 31.100000000000172
}
```

### Prerequisites

You will need access to the Climate Data Store API. Please retrieve your personal [CDSAPI key](https://cds.climate.copernicus.eu/how-to-api) and store it in `~/.cdsapirc`:

```bash
echo "url: https://cds.climate.copernicus.eu/api
key: INSERT-YOUR-KEY" > a
```

Then follow the steps below to set up a virtual Python environment and install dependencies:

```bash
cd data
python3 -m venv .venv
source .venv/bin/activate
pip3 install -U -r requirements.txt
```

### Execution

To run the parser, simply execute it. If you want to adjust the date range that will be downloaded, please edit the `main` method accordingly.

```bash
python3 parser.py
```

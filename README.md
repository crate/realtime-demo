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

#### Climate Data Store API

We retrieve data from the Climate Data Store API and you will need access to their API. Please retrieve your personal [CDSAPI key](https://cds.climate.copernicus.eu/how-to-api) and store it in `~/.cdsapirc`:

```bash
echo "url: https://cds.climate.copernicus.eu/api
key: INSERT-YOUR-KEY" > ~/.cdsapirc
```

#### AWS

We use Amazon Managed Streaming for Apache Kafka (MSK). Please set up credentials using [aws configure](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html#cli-configure-files-methods).

#### Producer

To run the producer, we need to set up a virtual Python environment and install dependencies:

```bash
cd data
python3 -m venv .venv
source .venv/bin/activate
pip3 install -U -r requirements.txt
```

Next, copy the example `.env` file and adjust values as needed:

```bash
cp .env.example .env
```

### Execution

To run the producer, simply execute it. If you want to adjust the date range that will be downloaded, please edit the `main` method accordingly.

```bash
python3 producer.py
```

## Trigger

The trigger is configured to fire on a single new Kafka (MSK) record (batch size 1). To restart the ingest from the start, delete the existing trigger and create a new one (it's very straightforward). There is only one option for MSK cluster, make sure authentication is set and to ignore bad test data, set the starting point to be the timestamp 2025-10-14T00:00:00.000Z. Set the topic to dev-1 (or a different topic as needed).
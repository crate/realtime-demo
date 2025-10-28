"""
A data producer that takes data from the parser and inserts it in a
configurable rate into AWS MSK.

The Kafka topic will be created if it doesn't exist yet.
"""

import os
import logging
import time
from parser import Parser
from dotenv import load_dotenv
from msk_kafka_admin import MSKKafkaAdmin
from msk_kafka_producer import MSKKafkaProducer

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

load_dotenv()

# The number of documents after which a log message is produced
# to communicate progress
PROGRESS_INDICATOR = 500


def main() -> None:
    """
    This is the main workflow execution, consisting of:
        1. Creating the Kafka topic, if it doesn't exist yet
        2. Downloading and parsing the source data
        3. Ingesting into AWS MSK
    """
    topic_name = os.environ["AWS_MSK_TOPIC_NAME"]

    kafka_admin = MSKKafkaAdmin(
        os.environ["AWS_REGION"],
        os.environ["AWS_MSK_BOOTSTRAP_SERVER"],
    )

    # Create the topic if it doesn't exist yet
    kafka_admin.topic_create(
        topic_name,
        int(os.environ["AWS_MSK_TOPIC_PARTITIONS"]),
        int(os.environ["AWS_MSK_TOPIC_REPLICATION"]),
    )

    # Generate the data we want to ingest
    parser = Parser("DEU")
    # The download_file method takes optional parameters if you want to change
    # the timeframe of the report.
    # Example for the 1st and 2nd of October 2025:
    #   download_file(2025, 10, ["01", "02"])
    if os.environ["SKIP_DOWNLOAD"].lower() in ["false", "0"]:
        logging.info("Downloading report")
        parser.download_file(2025, "08", ["10", "11", "12", "13", "14"])

    logging.info("Parsing report")
    json_documents_t2m = parser.to_json(
        "2m_temperature_0_daily-mean.nc", "t2m", "temperature"
    )
    json_documents_u10 = parser.to_json(
        "10m_u_component_of_wind_0_daily-mean.nc", "u10", "u10"
    )
    json_documents_v10 = parser.to_json(
        "10m_v_component_of_wind_0_daily-mean.nc", "v10", "v10"
    )
    json_documents_sp = parser.to_json(
        "surface_pressure_0_daily-mean.nc", "sp", "pressure"
    )

    logging.info(f"Found {len(json_documents_t2m)} t2m JSON documents to ingest")
    logging.info(f"Found {len(json_documents_u10)} u10 JSON documents to ingest")
    logging.info(f"Found {len(json_documents_v10)} v10 JSON documents to ingest")
    logging.info(f"Found {len(json_documents_sp)} sp JSON documents to ingest")

    # Now combine all into a single set of data
    json_documents = Parser.merge_json_documents(
        json_documents_t2m, json_documents_u10, json_documents_v10, json_documents_sp
    )
    logging.info(f"Merged into {len(json_documents)} combined documents")

    # Ingest the data into AWS MSK
    kafka_producer = MSKKafkaProducer(
        os.environ["AWS_REGION"],
        os.environ["AWS_MSK_BOOTSTRAP_SERVER"],
    )
    logging.info("Starting data ingestion")
    i = 0
    for document in json_documents:
        kafka_producer.send(topic_name, document)
        time.sleep(float(os.environ["PRODUCER_WAIT_TIME"]))

        i = i + 1
        if i % PROGRESS_INDICATOR == 0:
            logging.info("Sent %s documents", i)

    logging.info("Finished sending data")


if __name__ == "__main__":
    main()

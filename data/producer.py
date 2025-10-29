"""
A data producer that takes data from the parser and inserts it in a
configurable rate into AWS MSK.

The Kafka topic will be created if it doesn't exist yet.
"""

import os
import logging
import time
from climate_parser import ClimateParser
from dotenv import load_dotenv
from msk_kafka_admin import MSKKafkaAdmin
from msk_kafka_producer import MSKKafkaProducer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

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
    parser = ClimateParser("DEU")
    # The download_file method takes optional parameters if you want to change
    # the timeframe of the report.
    # Example for the 1st and 2nd of October 2025:
    #   download_file(2025, 10, ["01", "02"])
    if os.environ["SKIP_DOWNLOAD"].lower() in ["false", "0"]:
        logger.info("Downloading report")
        parser.download_file(2025, "08", ["10", "11", "12", "13", "14"])

    logger.info("Parsing report")
    json_documents = parser.to_json_combined()
    logger.info("Received %s combined JSON documents", len(json_documents))

    # Ingest the data into AWS MSK
    kafka_producer = MSKKafkaProducer(
        os.environ["AWS_REGION"],
        os.environ["AWS_MSK_BOOTSTRAP_SERVER"],
    )
    logger.info("Starting data ingestion")
    i = 0
    for document in json_documents:
        kafka_producer.send(topic_name, document)
        time.sleep(float(os.environ["PRODUCER_WAIT_TIME"]))

        i = i + 1
        if i % PROGRESS_INDICATOR == 0:
            logger.info("Sent %s documents", i)

    logger.info("Finished sending data")


if __name__ == "__main__":
    main()

import os
import logging
import json
import time
from dotenv import load_dotenv
from parser import Parser
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
PROGRESS_INDICATOR=500

def main() -> None:
    topic_name = os.environ["AWS_MKS_TOPIC_NAME"]

    kafka_admin = MSKKafkaAdmin(
        os.environ["AWS_REGION"],
        os.environ["AWS_MKS_BOOTSTRAP_SERVER"],
    )

    # Create the topic if it doesn't exist yet
    kafka_admin.topic_create(
        topic_name,
        int(os.environ["AWS_MKS_TOPIC_PARTITIONS"]),
        int(os.environ["AWS_MKS_TOPIC_REPLICATION"]),
    )

    # Generate the data we want to ingest, passing in an ISO-A3 code
    parser = Parser("NLD")
    
    # The download_file method takes optional parameters if you want to change
    # the timeframe of the report.
    # Example for the 1st and 2nd of October 2025:
    #   download_file(2025, 10, ["01", "02"])
    parser.download_file(2025, "08", ["10", "11", "12", "13", "14"])
    json_documents = parser.to_json()
    logging.info(f"Found {len(json_documents)} JSON documents to ingest")

    # Ingest the data into AWS MSK
    kafka_producer = MSKKafkaProducer(
        os.environ["AWS_REGION"],
        os.environ["AWS_MKS_BOOTSTRAP_SERVER"],
    )
    i = 0
    for document in json_documents:
#        print(document)
        kafka_producer.send(topic_name, document)
        time.sleep(float(os.environ["PRODUCER_WAIT_TIME"]))

        i = i + 1
        if i % PROGRESS_INDICATOR == 0:
            logging.info("Sent %s documents", i)

    logging.info("Reached the end of the data set")


if __name__ == "__main__":
    main()

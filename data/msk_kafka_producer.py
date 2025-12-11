"The producer that will write data into Kafka"

import logging
import json
from kafka import KafkaProducer


class MSKKafkaProducer:
    "A Kafka Producer class that instantiates a client and writes data"

    def __init__(self, aws_region: str, bootstrap_server: str) -> None:
        "Creates a new Kafka producer for a given bootstrap server URL"
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_server,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retry_backoff_ms=500,
            request_timeout_ms=20000,
            client_id="real-time-demo-producer",
        )

    def send(self, topic_name: str, value: str) -> None:
        "Sends data for a given topic to Kafka"
        try:
            _ = self.producer.send(topic_name, value=value)
            self.producer.flush()
        except Exception as e:
            logging.exception(e, stack_info=True)

"Encapsulates all functionality around administering Kafka"

import logging
from kafka.admin import KafkaAdminClient, NewTopic


class MSKKafkaAdmin:
    "A Kafka administration client"

    def __init__(self, aws_region: str, bootstrap_server: str) -> None:
        "Initializes the client for a given bootstrap server"
        self.client = KafkaAdminClient(
            bootstrap_servers=bootstrap_server,
            client_id="real-time-demo-producer",
        )

    def topic_create(
        self,
        topic_name: str,
        num_partitions: int,
        replication_factor: int,
    ) -> None:
        "Creates the topic if it doesn't exist yet"
        topic_list = [
            NewTopic(
                name=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
            )
        ]

        if topic_name not in self.client.list_topics():
            self.client.create_topics(topic_list)
            logging.info("Topic %s has been created successfully", topic_name)
        else:
            logging.info(
                "Skipping creation of topic %s because it already exists", topic_name
            )

from kafka.sasl.oauth import AbstractTokenProvider
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

"Class to provide MSK authentication token"


class MSKTokenProvider(AbstractTokenProvider):
    "Taken from https://aws.amazon.com/blogs/big-data/build-an-end-to-end-serverless-streaming-pipeline-with-apache-kafka-on-amazon-msk-using-python/"

    def __init__(self, aws_region: str) -> None:
        self.aws_region = aws_region

    def token(self) -> str:
        "Returns a token"
        token, _ = MSKAuthTokenProvider.generate_auth_token(self.aws_region)
        return token

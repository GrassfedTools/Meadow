import boto3
import pytest
from moto import mock_dynamodb2, mock_s3, mock_ses, mock_ssm


@pytest.fixture(scope="function")
def initialise():
    # Mock endpoints
    mockdynamodb2 = mock_dynamodb2()
    mockssm = mock_ssm()
    mockses = mock_ses()
    mocks3 = mock_s3()

    # Start endpoints
    mockdynamodb2.start()
    mockssm.start()
    mockses.start()
    mocks3.start()
    boto3.setup_default_session()

    # Create mock verified SES users
    ses = boto3.client("ses")
    ses.verify_email_identity(EmailAddress="noreply@meadow.test")
    ses.verify_email_identity(EmailAddress="test@test.test")

    # Create mock users DynamoDB table
    ddb = boto3.client("dynamodb")
    ddb.create_table(
        AttributeDefinitions=[
            {"AttributeName": "partitionKey", "AttributeType": "S"},
            {"AttributeName": "sortKey", "AttributeType": "S"},
            {"AttributeName": "is_subscribed", "AttributeType": "S"},
        ],
        TableName="meadow-users",
        KeySchema=[
            {
                "AttributeName": "partitionKey",
                "KeyType": "HASH",
            },
            {
                "AttributeName": "sortKey",
                "KeyType": "RANGE",
            },
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "is_subscribed",
                "KeySchema": [
                    {"AttributeName": "is_subscribed", "KeyType": "HASH"},
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": [
                        "partitionKey",
                    ],
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 1,
                    "WriteCapacityUnits": 1,
                },
            },
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    # Create mock SSM
    ssm = boto3.client("ssm")
    ssm.put_parameter(
        Name="MeadowDictionary",
        Value=(
            '{ "organisation": "Meadow Testing","table": "meadow-users", '
            '"meadow_domain": "meadow.test", "website_domain": "test", '
            '"region": "us-east-1", "honeypot_secret": "11111111", "barn": "my-barn" }'
        ),
        Type="String",
    )

    # Create mock s3 barn
    s3 = boto3.client("s3")
    mock_email = """
    Did you sign up to this newsletter?
    If so, follow this path: {{ validation_path }}

    To unsubscribe, click here: {{ unsubscribe_path }}
    ---TEXT-HTML-SEPARATOR---
    Did you sign up to this newsletter?
    If so, follow this path: {{ validation_path }}

    To unsubscribe, click here: {{ unsubscribe_path }}
    """.encode(
        "utf-8"
    )
    s3.create_bucket(
        Bucket="my-barn", CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
    )
    s3.put_object(Body=mock_email, Bucket="my-barn", Key="transactional/validate.j2")
    s3.put_object(Body=mock_email, Bucket="my-barn", Key="newsletters/20210421.j2")

    yield ddb, ssm, ses, s3

    # Stop endpoints
    mockdynamodb2.stop()
    mockssm.stop()
    mockses.stop()
    mocks3.stop()

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

    # Start endpoints. Mock SES users, DynamoDB table and SSM
    ddb, ssm, ses = baseInitialise(mockdynamodb2, mockssm, mockses, mocks3)

    # Create mock s3 barn
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

    s3 = mockBarn(mock_email)

    yield ddb, ssm, ses, s3

    # Stop endpoints
    mockdynamodb2.stop()
    mockssm.stop()
    mockses.stop()
    mocks3.stop()


@pytest.fixture(scope="function")
def initialiseWithEmptyHtmlTemplate():
    # Mock endpoints
    mockdynamodb2 = mock_dynamodb2()
    mockssm = mock_ssm()
    mockses = mock_ses()
    mocks3 = mock_s3()

    # Start endpoints. Mock SES users, DynamoDB table and SSM
    ddb, ssm, ses = baseInitialise(mockdynamodb2, mockssm, mockses, mocks3)

    # Create mock s3 barn
    mock_email = """
    ---TEXT-HTML-SEPARATOR---
    Did you sign up to this newsletter?
    If so, follow this path: {{ validation_path }}

    To unsubscribe, click here: {{ unsubscribe_path }}
    """

    s3 = mockBarn(mock_email)

    yield ddb, ssm, ses, s3

    # Stop endpoints
    mockdynamodb2.stop()
    mockssm.stop()
    mockses.stop()
    mocks3.stop()


@pytest.fixture(scope="function")
def initialiseWithEmptyTextTemplate():
    # Mock endpoints
    mockdynamodb2 = mock_dynamodb2()
    mockssm = mock_ssm()
    mockses = mock_ses()
    mocks3 = mock_s3()

    # Start endpoints. Mock SES users, DynamoDB table and SSM
    ddb, ssm, ses = baseInitialise(mockdynamodb2, mockssm, mockses, mocks3)

    # Create mock s3 barn
    mock_email = """
    Did you sign up to this newsletter?
    If so, follow this path: {{ validation_path }}

    To unsubscribe, click here: {{ unsubscribe_path }}
    ---TEXT-HTML-SEPARATOR---
    """.encode(
        "utf-8"
    )

    s3 = mockBarn(mock_email)

    yield ddb, ssm, ses, s3

    # Stop endpoints
    mockdynamodb2.stop()
    mockssm.stop()
    mockses.stop()
    mocks3.stop()


@pytest.fixture(scope="function")
def initialiseTemplateWithIncorrectSeperator():
    # Mock endpoints
    mockdynamodb2 = mock_dynamodb2()
    mockssm = mock_ssm()
    mockses = mock_ses()
    mocks3 = mock_s3()

    # Start endpoints. Mock SES users, DynamoDB table and SSM
    ddb, ssm, ses = baseInitialise(mockdynamodb2, mockssm, mockses, mocks3)

    # Create mock s3 barn
    mock_email = """
    Did you sign up to this newsletter?
    If so, follow this path: {{ validation_path }}

    To unsubscribe, click here: {{ unsubscribe_path }}
    ---TEXT--SEPARATOR---
    Did you sign up to this newsletter?
    If so, follow this path: {{ validation_path }}

    To unsubscribe, click here: {{ unsubscribe_path }}
    """.encode(
        "utf-8"
    )

    s3 = mockBarn(mock_email)

    yield ddb, ssm, ses, s3

    # Stop endpoints
    mockdynamodb2.stop()
    mockssm.stop()
    mockses.stop()
    mocks3.stop()


@pytest.fixture(scope="function")
def initialiseTemplateWithoutBody():
    # Mock endpoints
    mockdynamodb2 = mock_dynamodb2()
    mockssm = mock_ssm()
    mockses = mock_ses()
    mocks3 = mock_s3()

    # Start endpoints. Mock SES users, DynamoDB table and SSM
    ddb, ssm, ses = baseInitialise(mockdynamodb2, mockssm, mockses, mocks3)

    # Create mock s3 barn
    s3 = boto3.client("s3", region_name="us-east-1")

    s3.create_bucket(
        Bucket="my-barn", CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
    )
    s3.put_object(Bucket="my-barn", Key="transactional/validate.j2")
    s3.put_object(Bucket="my-barn", Key="newsletters/20210421.j2")

    yield ddb, ssm, ses, s3

    # Stop endpoints
    mockdynamodb2.stop()
    mockssm.stop()
    mockses.stop()
    mocks3.stop()


def baseInitialise(mockdynamodb2, mockssm, mockses, mocks3):
    # Start endpoints
    mockdynamodb2.start()
    mockssm.start()
    mockses.start()
    mocks3.start()
    boto3.setup_default_session()

    # Create mock verified SES users
    ses = boto3.client("ses", region_name="us-east-1")
    ses.verify_email_identity(EmailAddress="noreply@meadow.test")
    ses.verify_email_identity(EmailAddress="test@test.test")

    # Create mock users DynamoDB table
    ddb = boto3.client("dynamodb", region_name="us-east-1")
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
    ssm = boto3.client("ssm", region_name="us-east-1")
    ssm.put_parameter(
        Name="MeadowDictionary",
        Value=(
            '{ "organisation": "Meadow Testing","table": "meadow-users", '
            '"meadow_domain": "meadow.test", "website_domain": "test", '
            '"region": "us-east-1", "honeypot_secret": "11111111", "barn": "my-barn" }'
        ),
        Type="String",
    )

    return ddb, ssm, ses


def mockBarn(body):
    s3 = boto3.client("s3", region_name="us-east-1")

    s3.create_bucket(
        Bucket="my-barn", CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
    )
    s3.put_object(Body=body, Bucket="my-barn", Key="transactional/validate.j2")
    s3.put_object(Body=body, Bucket="my-barn", Key="newsletters/20210421.j2")

    return s3

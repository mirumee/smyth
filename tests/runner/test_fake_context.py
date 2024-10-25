from time import strftime

import pytest

from smyth.runner.fake_context import FakeLambdaContext


def test_fake_lambda_context():
    context = FakeLambdaContext()
    assert context.function_name == "Fake"
    assert context.function_version == "LATEST"
    assert context.invoked_function_arn == "arn:aws:lambda:serverless:Fake"
    assert context.memory_limit_in_mb == "1024"
    assert context.aws_request_id == "1234567890"
    assert context.log_group_name == "/aws/lambda/Fake"
    assert context.log_stream_name == (
        f"{strftime('%Y/%m/%d')}/[$LATEST]58419525dade4d17a495dceeeed44708"
    )


@pytest.mark.parametrize(
    (
        "name",
        "version",
        "timeout",
        "expected_name",
        "expected_version",
        "expected_timeout",
    ),
    [
        ("test", "test", 60, "test", "test", 60),
        ("test", "test", None, "test", "test", 6),
        ("test", None, 120, "test", "LATEST", 120),
        (None, "test", 6, "Fake", "test", 6),
        (None, None, 6, "Fake", "LATEST", 6),
    ],
)
def test_fake_lambda_context_with_params(
    name, version, timeout, expected_name, expected_version, expected_timeout
):
    context = FakeLambdaContext(name=name, version=version, timeout=timeout)
    assert context.function_name == expected_name
    assert context.function_version == expected_version
    assert context.timeout == expected_timeout
    assert context.invoked_function_arn == f"arn:aws:lambda:serverless:{expected_name}"
    assert context.memory_limit_in_mb == "1024"
    assert context.aws_request_id == "1234567890"
    assert context.log_group_name == f"/aws/lambda/{expected_name}"
    assert context.log_stream_name == (
        f"{strftime('%Y/%m/%d')}/[${expected_version}]58419525dade4d17a495dceeeed44708"
    )

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_mock import MockerFixture

from smyth.runner.fake_context import FakeLambdaContext


def test_fake_lambda_context(freezer: FrozenDateTimeFactory, mocker: MockerFixture):
    freezer.move_to("2024-12-20 00:00:00")
    expected_name = "Test Name Set In Test"
    environ = mocker.patch.dict("os.environ", clear=True)
    environ.update(
        {
            "AWS_LAMBDA_FUNCTION_NAME": expected_name,
        }
    )
    context = FakeLambdaContext()

    assert context.function_name == expected_name
    assert context.function_version == "$LATEST"
    assert context.invoked_function_arn == f"arn:aws:lambda:serverless:{expected_name}"
    assert context.memory_limit_in_mb == "128"
    assert context.aws_request_id == "1234567890"
    assert context.log_group_name == f"/aws/lambda/{expected_name}"
    assert context.log_stream_name == (
        "2024/12/20/[$LATEST]smyth_aws_lambda_log_stream_name"
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
        ("test", None, 120, "test", "$LATEST", 120),
        (None, "test", 6, "Fake", "test", 6),
        (None, None, 6, "Fake", "$LATEST", 6),
    ],
)
def test_fake_lambda_context_with_params(
    name,
    version,
    timeout,
    expected_name,
    expected_version,
    expected_timeout,
    freezer: FrozenDateTimeFactory,
):
    freezer.move_to("2024-12-20 00:00:00")
    context = FakeLambdaContext(name=name, version=version, timeout=timeout)
    assert context.function_name == expected_name
    assert context.function_version == expected_version
    assert context._timeout == expected_timeout
    assert context.invoked_function_arn == f"arn:aws:lambda:serverless:{expected_name}"
    assert context.memory_limit_in_mb == "128"
    assert context.aws_request_id == "1234567890"
    assert context.log_group_name == f"/aws/lambda/{expected_name}"
    assert context.log_stream_name == (
        f"2024/12/20/[{expected_version}]smyth_aws_lambda_log_stream_name"
    )

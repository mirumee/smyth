from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RunnerResultType(StrEnum):
    HTTP = "HTTP"
    EXCEPTION = "EXCEPTION"


class LambdaHttpResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    is_base64_encoded: bool = Field(..., alias="isBase64Encoded")
    status_code: int = Field(..., description="HTTP status code", alias="statusCode")
    headers: dict[str, str]
    body: str


class LambdaExceptionResponse(BaseModel):
    message: str
    type: str
    stack_trace: str


class RunnerResult(BaseModel):
    type: RunnerResultType
    response: LambdaHttpResponse | LambdaExceptionResponse


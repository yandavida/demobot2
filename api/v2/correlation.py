import uuid
from fastapi import Request, Response

CORRELATION_ID_HEADER = "X-Correlation-Id"

def get_or_create_correlation_id(request: Request) -> str:
    cid = request.headers.get(CORRELATION_ID_HEADER)
    if not cid:
        cid = uuid.uuid4().hex
    request.state.correlation_id = cid
    return cid

def attach_correlation_id(response: Response, cid: str) -> None:
    response.headers[CORRELATION_ID_HEADER] = cid

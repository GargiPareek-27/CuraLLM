"""HTTP client for the inference service.

Timeouts are explicit. Only connection failures (nothing was delivered) are
retried, with bounded exponential backoff. Read timeouts are not retried
because the request may already have been processed.
"""
import asyncio
from dataclasses import dataclass

import httpx

from app.retry import backoff_delay


class InferenceError(Exception):
    """Base class for inference failures."""


class InferenceUnavailable(InferenceError):
    pass


class InferenceTimeout(InferenceError):
    pass


class InferenceBadResponse(InferenceError):
    pass


@dataclass(frozen=True)
class InferenceResult:
    text: str
    model_id: str
    model_revision: str
    is_mock: bool


def _parse_result(response: httpx.Response) -> InferenceResult:
    try:
        data = response.json()
    except ValueError as exc:
        raise InferenceBadResponse("Response was not valid JSON.") from exc
    if not isinstance(data, dict):
        raise InferenceBadResponse("Response JSON was not an object.")
    try:
        text, model_id = data["text"], data["model_id"]
        revision, is_mock = data["model_revision"], data["is_mock"]
    except KeyError as exc:
        raise InferenceBadResponse("Response was missing a required field.") from exc
    if not (
        isinstance(text, str)
        and isinstance(model_id, str)
        and isinstance(revision, str)
        and isinstance(is_mock, bool)
    ):
        raise InferenceBadResponse("Response had a field of the wrong type.")
    return InferenceResult(text=text, model_id=model_id, model_revision=revision, is_mock=is_mock)


class InferenceClient:
    def __init__(
        self,
        base_url: str,
        connect_timeout: float,
        read_timeout: float,
        max_retries: int,
        max_concurrency: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(
                connect=connect_timeout, read=read_timeout, write=5.0, pool=5.0
            ),
            transport=transport,
        )
        self._max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _post_with_retries(self, payload: dict) -> httpx.Response:
        attempt = 0
        while True:
            try:
                return await self._client.post("/v1/generate", json=payload)
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                # Nothing reached the service, so retrying cannot duplicate work.
                if attempt >= self._max_retries:
                    raise InferenceUnavailable("Could not connect to inference.") from exc
                await asyncio.sleep(backoff_delay(attempt))
                attempt += 1
            except httpx.TimeoutException as exc:
                # The service may already have received the request: never retry this.
                raise InferenceTimeout("Inference did not answer in time.") from exc
            except httpx.HTTPError as exc:
                raise InferenceUnavailable("Inference request failed.") from exc

    async def generate(
        self, prompt: str, max_tokens: int = 512, request_id: str | None = None
    ) -> InferenceResult:
        payload = {"prompt": prompt, "max_tokens": max_tokens, "request_id": request_id}
        async with self._semaphore:
            response = await self._post_with_retries(payload)

        if response.status_code == 504:
            raise InferenceTimeout("Inference reported a timeout.")
        if response.status_code == 503:
            raise InferenceUnavailable("Inference reported it is unavailable.")
        if response.status_code != 200:
            raise InferenceBadResponse(f"Unexpected status {response.status_code}.")
        return _parse_result(response)

    async def health(self) -> bool:
        try:
            response = await self._client.get("/health")
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    async def aclose(self) -> None:
        await self._client.aclose()

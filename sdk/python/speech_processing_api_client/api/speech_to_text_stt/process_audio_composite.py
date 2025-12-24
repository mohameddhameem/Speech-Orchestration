from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.transcription_request import TranscriptionRequest
from ...models.transcription_response import TranscriptionResponse
from typing import cast



def _get_kwargs(
    *,
    body: TranscriptionRequest,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/stt/process",
    }

    _kwargs["json"] = body.to_dict()


    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | TranscriptionResponse | None:
    if response.status_code == 202:
        response_202 = TranscriptionResponse.from_dict(response.json())



        return response_202

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | TranscriptionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TranscriptionRequest,

) -> Response[Any | TranscriptionResponse]:
    r""" Unified Pipeline (Detect + Transcribe + Translate)

     \"Fire and forget\" composite job. Performs language detection, transcription,
    and optional translation in a single async workflow.
    Ideal for automated pipelines where the source language is unknown.

    Args:
        body (TranscriptionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | TranscriptionResponse]
     """


    kwargs = _get_kwargs(
        body=body,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    body: TranscriptionRequest,

) -> Any | TranscriptionResponse | None:
    r""" Unified Pipeline (Detect + Transcribe + Translate)

     \"Fire and forget\" composite job. Performs language detection, transcription,
    and optional translation in a single async workflow.
    Ideal for automated pipelines where the source language is unknown.

    Args:
        body (TranscriptionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | TranscriptionResponse
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TranscriptionRequest,

) -> Response[Any | TranscriptionResponse]:
    r""" Unified Pipeline (Detect + Transcribe + Translate)

     \"Fire and forget\" composite job. Performs language detection, transcription,
    and optional translation in a single async workflow.
    Ideal for automated pipelines where the source language is unknown.

    Args:
        body (TranscriptionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | TranscriptionResponse]
     """


    kwargs = _get_kwargs(
        body=body,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TranscriptionRequest,

) -> Any | TranscriptionResponse | None:
    r""" Unified Pipeline (Detect + Transcribe + Translate)

     \"Fire and forget\" composite job. Performs language detection, transcription,
    and optional translation in a single async workflow.
    Ideal for automated pipelines where the source language is unknown.

    Args:
        body (TranscriptionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | TranscriptionResponse
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed

from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.error_response import ErrorResponse
from ...models.transcribe_audio_files_body import TranscribeAudioFilesBody
from ...models.transcription_request import TranscriptionRequest
from ...models.transcription_response import TranscriptionResponse
from typing import cast



def _get_kwargs(
    *,
    body:    TranscribeAudioFilesBody  |     TranscriptionRequest  | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/speech-to-text/transcribe",
    }

    if isinstance(body, TranscribeAudioFilesBody):
        _kwargs["files"] = body.to_multipart()


        headers["Content-Type"] = "multipart/form-data"
    if isinstance(body, TranscriptionRequest):
        _kwargs["json"] = body.to_dict()


        headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | ErrorResponse | TranscriptionResponse | None:
    if response.status_code == 202:
        response_202 = TranscriptionResponse.from_dict(response.json())



        return response_202

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())



        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 413:
        response_413 = cast(Any, None)
        return response_413

    if response.status_code == 429:
        response_429 = cast(Any, None)
        return response_429

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())



        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | ErrorResponse | TranscriptionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body:    TranscribeAudioFilesBody  |     TranscriptionRequest  | Unset = UNSET,

) -> Response[Any | ErrorResponse | TranscriptionResponse]:
    """ Transcribe audio to text

     Submit audio for transcription via direct upload or Azure Blob reference.
    Supports both batch and near-real-time processing modes.
    Returns immediately with job_id for async polling.

    Args:
        body (TranscribeAudioFilesBody):
        body (TranscriptionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorResponse | TranscriptionResponse]
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
    body:    TranscribeAudioFilesBody  |     TranscriptionRequest  | Unset = UNSET,

) -> Any | ErrorResponse | TranscriptionResponse | None:
    """ Transcribe audio to text

     Submit audio for transcription via direct upload or Azure Blob reference.
    Supports both batch and near-real-time processing modes.
    Returns immediately with job_id for async polling.

    Args:
        body (TranscribeAudioFilesBody):
        body (TranscriptionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorResponse | TranscriptionResponse
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body:    TranscribeAudioFilesBody  |     TranscriptionRequest  | Unset = UNSET,

) -> Response[Any | ErrorResponse | TranscriptionResponse]:
    """ Transcribe audio to text

     Submit audio for transcription via direct upload or Azure Blob reference.
    Supports both batch and near-real-time processing modes.
    Returns immediately with job_id for async polling.

    Args:
        body (TranscribeAudioFilesBody):
        body (TranscriptionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorResponse | TranscriptionResponse]
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
    body:    TranscribeAudioFilesBody  |     TranscriptionRequest  | Unset = UNSET,

) -> Any | ErrorResponse | TranscriptionResponse | None:
    """ Transcribe audio to text

     Submit audio for transcription via direct upload or Azure Blob reference.
    Supports both batch and near-real-time processing modes.
    Returns immediately with job_id for async polling.

    Args:
        body (TranscribeAudioFilesBody):
        body (TranscriptionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorResponse | TranscriptionResponse
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed

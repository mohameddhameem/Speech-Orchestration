from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.get_available_voices_response_200 import GetAvailableVoicesResponse200
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    *,
    language: str | Unset = UNSET,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    params["language"] = language


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/available-voices",
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> GetAvailableVoicesResponse200 | None:
    if response.status_code == 200:
        response_200 = GetAvailableVoicesResponse200.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[GetAvailableVoicesResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    language: str | Unset = UNSET,

) -> Response[GetAvailableVoicesResponse200]:
    """ List available TTS voices

     Get list of supported neural voices per language

    Args:
        language (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAvailableVoicesResponse200]
     """


    kwargs = _get_kwargs(
        language=language,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    language: str | Unset = UNSET,

) -> GetAvailableVoicesResponse200 | None:
    """ List available TTS voices

     Get list of supported neural voices per language

    Args:
        language (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAvailableVoicesResponse200
     """


    return sync_detailed(
        client=client,
language=language,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    language: str | Unset = UNSET,

) -> Response[GetAvailableVoicesResponse200]:
    """ List available TTS voices

     Get list of supported neural voices per language

    Args:
        language (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAvailableVoicesResponse200]
     """


    kwargs = _get_kwargs(
        language=language,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    language: str | Unset = UNSET,

) -> GetAvailableVoicesResponse200 | None:
    """ List available TTS voices

     Get list of supported neural voices per language

    Args:
        language (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAvailableVoicesResponse200
     """


    return (await asyncio_detailed(
        client=client,
language=language,

    )).parsed

from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.job_status_response import JobStatusResponse
from typing import cast
from uuid import UUID



def _get_kwargs(
    job_id: UUID,

) -> dict[str, Any]:
    

    

    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/jobs/{job_id}".format(job_id=quote(str(job_id), safe=""),),
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | JobStatusResponse | None:
    if response.status_code == 200:
        response_200 = JobStatusResponse.from_dict(response.json())



        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if response.status_code == 410:
        response_410 = cast(Any, None)
        return response_410

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | JobStatusResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: UUID,
    *,
    client: AuthenticatedClient | Client,

) -> Response[Any | JobStatusResponse]:
    """ Get job status and details

     Poll for job completion status. Use exponential backoff:
    - Initial: 1 second
    - Max: 30 seconds
    - Backoff multiplier: 1.5

    Args:
        job_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | JobStatusResponse]
     """


    kwargs = _get_kwargs(
        job_id=job_id,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    job_id: UUID,
    *,
    client: AuthenticatedClient | Client,

) -> Any | JobStatusResponse | None:
    """ Get job status and details

     Poll for job completion status. Use exponential backoff:
    - Initial: 1 second
    - Max: 30 seconds
    - Backoff multiplier: 1.5

    Args:
        job_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | JobStatusResponse
     """


    return sync_detailed(
        job_id=job_id,
client=client,

    ).parsed

async def asyncio_detailed(
    job_id: UUID,
    *,
    client: AuthenticatedClient | Client,

) -> Response[Any | JobStatusResponse]:
    """ Get job status and details

     Poll for job completion status. Use exponential backoff:
    - Initial: 1 second
    - Max: 30 seconds
    - Backoff multiplier: 1.5

    Args:
        job_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | JobStatusResponse]
     """


    kwargs = _get_kwargs(
        job_id=job_id,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    job_id: UUID,
    *,
    client: AuthenticatedClient | Client,

) -> Any | JobStatusResponse | None:
    """ Get job status and details

     Poll for job completion status. Use exponential backoff:
    - Initial: 1 second
    - Max: 30 seconds
    - Backoff multiplier: 1.5

    Args:
        job_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | JobStatusResponse
     """


    return (await asyncio_detailed(
        job_id=job_id,
client=client,

    )).parsed

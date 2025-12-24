from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.jobs_list import JobsList
from ...models.list_jobs_job_type import ListJobsJobType
from ...models.list_jobs_status import ListJobsStatus
from ...types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
import datetime



def _get_kwargs(
    *,
    status: ListJobsStatus | Unset = UNSET,
    job_type: ListJobsJobType | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 20,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    json_status: str | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    json_job_type: str | Unset = UNSET
    if not isinstance(job_type, Unset):
        json_job_type = job_type.value

    params["job_type"] = json_job_type

    json_created_after: str | Unset = UNSET
    if not isinstance(created_after, Unset):
        json_created_after = created_after.isoformat()
    params["created_after"] = json_created_after

    params["page"] = page

    params["page_size"] = page_size


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/jobs",
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | JobsList | None:
    if response.status_code == 200:
        response_200 = JobsList.from_dict(response.json())



        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | JobsList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: ListJobsStatus | Unset = UNSET,
    job_type: ListJobsJobType | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 20,

) -> Response[Any | JobsList]:
    """ List user's jobs

     List all jobs with filtering and pagination

    Args:
        status (ListJobsStatus | Unset):
        job_type (ListJobsJobType | Unset):
        created_after (datetime.datetime | Unset):
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | JobsList]
     """


    kwargs = _get_kwargs(
        status=status,
job_type=job_type,
created_after=created_after,
page=page,
page_size=page_size,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    status: ListJobsStatus | Unset = UNSET,
    job_type: ListJobsJobType | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 20,

) -> Any | JobsList | None:
    """ List user's jobs

     List all jobs with filtering and pagination

    Args:
        status (ListJobsStatus | Unset):
        job_type (ListJobsJobType | Unset):
        created_after (datetime.datetime | Unset):
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | JobsList
     """


    return sync_detailed(
        client=client,
status=status,
job_type=job_type,
created_after=created_after,
page=page,
page_size=page_size,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: ListJobsStatus | Unset = UNSET,
    job_type: ListJobsJobType | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 20,

) -> Response[Any | JobsList]:
    """ List user's jobs

     List all jobs with filtering and pagination

    Args:
        status (ListJobsStatus | Unset):
        job_type (ListJobsJobType | Unset):
        created_after (datetime.datetime | Unset):
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | JobsList]
     """


    kwargs = _get_kwargs(
        status=status,
job_type=job_type,
created_after=created_after,
page=page,
page_size=page_size,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    status: ListJobsStatus | Unset = UNSET,
    job_type: ListJobsJobType | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 20,

) -> Any | JobsList | None:
    """ List user's jobs

     List all jobs with filtering and pagination

    Args:
        status (ListJobsStatus | Unset):
        job_type (ListJobsJobType | Unset):
        created_after (datetime.datetime | Unset):
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | JobsList
     """


    return (await asyncio_detailed(
        client=client,
status=status,
job_type=job_type,
created_after=created_after,
page=page,
page_size=page_size,

    )).parsed

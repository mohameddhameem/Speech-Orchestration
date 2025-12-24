from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.job_status_response_job_type import JobStatusResponseJobType
from ..models.job_status_response_status import JobStatusResponseStatus
from ..types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
from uuid import UUID
import datetime

if TYPE_CHECKING:
  from ..models.error_detail import ErrorDetail





T = TypeVar("T", bound="JobStatusResponse")



@_attrs_define
class JobStatusResponse:
    """ 
        Attributes:
            job_id (UUID | Unset):
            job_type (JobStatusResponseJobType | Unset):
            status (JobStatusResponseStatus | Unset):
            created_at (datetime.datetime | Unset):
            completed_at (datetime.datetime | Unset):
            progress_percent (int | Unset):
            queue_position (int | Unset): Current position in processing queue (if pending)
            estimated_wait_minutes (float | Unset): Estimated wait time in minutes (if pending)
            error (ErrorDetail | Unset):
     """

    job_id: UUID | Unset = UNSET
    job_type: JobStatusResponseJobType | Unset = UNSET
    status: JobStatusResponseStatus | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    completed_at: datetime.datetime | Unset = UNSET
    progress_percent: int | Unset = UNSET
    queue_position: int | Unset = UNSET
    estimated_wait_minutes: float | Unset = UNSET
    error: ErrorDetail | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.error_detail import ErrorDetail
        job_id: str | Unset = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        job_type: str | Unset = UNSET
        if not isinstance(self.job_type, Unset):
            job_type = self.job_type.value


        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value


        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        completed_at: str | Unset = UNSET
        if not isinstance(self.completed_at, Unset):
            completed_at = self.completed_at.isoformat()

        progress_percent = self.progress_percent

        queue_position = self.queue_position

        estimated_wait_minutes = self.estimated_wait_minutes

        error: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error, Unset):
            error = self.error.to_dict()


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if job_id is not UNSET:
            field_dict["job_id"] = job_id
        if job_type is not UNSET:
            field_dict["job_type"] = job_type
        if status is not UNSET:
            field_dict["status"] = status
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at
        if progress_percent is not UNSET:
            field_dict["progress_percent"] = progress_percent
        if queue_position is not UNSET:
            field_dict["queue_position"] = queue_position
        if estimated_wait_minutes is not UNSET:
            field_dict["estimated_wait_minutes"] = estimated_wait_minutes
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_detail import ErrorDetail
        d = dict(src_dict)
        _job_id = d.pop("job_id", UNSET)
        job_id: UUID | Unset
        if isinstance(_job_id,  Unset):
            job_id = UNSET
        else:
            job_id = UUID(_job_id)




        _job_type = d.pop("job_type", UNSET)
        job_type: JobStatusResponseJobType | Unset
        if isinstance(_job_type,  Unset):
            job_type = UNSET
        else:
            job_type = JobStatusResponseJobType(_job_type)




        _status = d.pop("status", UNSET)
        status: JobStatusResponseStatus | Unset
        if isinstance(_status,  Unset):
            status = UNSET
        else:
            status = JobStatusResponseStatus(_status)




        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _completed_at = d.pop("completed_at", UNSET)
        completed_at: datetime.datetime | Unset
        if isinstance(_completed_at,  Unset):
            completed_at = UNSET
        else:
            completed_at = isoparse(_completed_at)




        progress_percent = d.pop("progress_percent", UNSET)

        queue_position = d.pop("queue_position", UNSET)

        estimated_wait_minutes = d.pop("estimated_wait_minutes", UNSET)

        _error = d.pop("error", UNSET)
        error: ErrorDetail | Unset
        if isinstance(_error,  Unset):
            error = UNSET
        else:
            error = ErrorDetail.from_dict(_error)




        job_status_response = cls(
            job_id=job_id,
            job_type=job_type,
            status=status,
            created_at=created_at,
            completed_at=completed_at,
            progress_percent=progress_percent,
            queue_position=queue_position,
            estimated_wait_minutes=estimated_wait_minutes,
            error=error,
        )


        job_status_response.additional_properties = d
        return job_status_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

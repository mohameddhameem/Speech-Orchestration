from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.text_to_speech_response_status import TextToSpeechResponseStatus
from ..types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
from uuid import UUID
import datetime

if TYPE_CHECKING:
  from ..models.error_detail import ErrorDetail





T = TypeVar("T", bound="TextToSpeechResponse")



@_attrs_define
class TextToSpeechResponse:
    """ 
        Attributes:
            job_id (UUID | Unset):
            status (TextToSpeechResponseStatus | Unset):
            created_at (datetime.datetime | Unset):
            audio_format (str | Unset):
            audio_duration_seconds (float | Unset):
            download_url (str | Unset): Blob URI for accessing audio. Client should use DefaultAzureCredential to download.
            processing_time_seconds (float | Unset):
            error (ErrorDetail | Unset):
     """

    job_id: UUID | Unset = UNSET
    status: TextToSpeechResponseStatus | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    audio_format: str | Unset = UNSET
    audio_duration_seconds: float | Unset = UNSET
    download_url: str | Unset = UNSET
    processing_time_seconds: float | Unset = UNSET
    error: ErrorDetail | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.error_detail import ErrorDetail
        job_id: str | Unset = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value


        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        audio_format = self.audio_format

        audio_duration_seconds = self.audio_duration_seconds

        download_url = self.download_url

        processing_time_seconds = self.processing_time_seconds

        error: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error, Unset):
            error = self.error.to_dict()


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if job_id is not UNSET:
            field_dict["job_id"] = job_id
        if status is not UNSET:
            field_dict["status"] = status
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if audio_format is not UNSET:
            field_dict["audio_format"] = audio_format
        if audio_duration_seconds is not UNSET:
            field_dict["audio_duration_seconds"] = audio_duration_seconds
        if download_url is not UNSET:
            field_dict["download_url"] = download_url
        if processing_time_seconds is not UNSET:
            field_dict["processing_time_seconds"] = processing_time_seconds
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




        _status = d.pop("status", UNSET)
        status: TextToSpeechResponseStatus | Unset
        if isinstance(_status,  Unset):
            status = UNSET
        else:
            status = TextToSpeechResponseStatus(_status)




        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        audio_format = d.pop("audio_format", UNSET)

        audio_duration_seconds = d.pop("audio_duration_seconds", UNSET)

        download_url = d.pop("download_url", UNSET)

        processing_time_seconds = d.pop("processing_time_seconds", UNSET)

        _error = d.pop("error", UNSET)
        error: ErrorDetail | Unset
        if isinstance(_error,  Unset):
            error = UNSET
        else:
            error = ErrorDetail.from_dict(_error)




        text_to_speech_response = cls(
            job_id=job_id,
            status=status,
            created_at=created_at,
            audio_format=audio_format,
            audio_duration_seconds=audio_duration_seconds,
            download_url=download_url,
            processing_time_seconds=processing_time_seconds,
            error=error,
        )


        text_to_speech_response.additional_properties = d
        return text_to_speech_response

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

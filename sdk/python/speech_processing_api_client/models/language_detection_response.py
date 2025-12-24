from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.language_detection_response_status import LanguageDetectionResponseStatus
from ..types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
from uuid import UUID
import datetime

if TYPE_CHECKING:
  from ..models.language_detection_response_languages_item import LanguageDetectionResponseLanguagesItem
  from ..models.error_detail import ErrorDetail





T = TypeVar("T", bound="LanguageDetectionResponse")



@_attrs_define
class LanguageDetectionResponse:
    """ 
        Attributes:
            job_id (UUID | Unset):
            status (LanguageDetectionResponseStatus | Unset):
            created_at (datetime.datetime | Unset):
            languages (list[LanguageDetectionResponseLanguagesItem] | Unset): Detected languages sorted by confidence
                (highest first)
            primary_language (str | Unset): Most confident language detection
            processing_time_seconds (float | Unset):
            error (ErrorDetail | Unset):
     """

    job_id: UUID | Unset = UNSET
    status: LanguageDetectionResponseStatus | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    languages: list[LanguageDetectionResponseLanguagesItem] | Unset = UNSET
    primary_language: str | Unset = UNSET
    processing_time_seconds: float | Unset = UNSET
    error: ErrorDetail | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.language_detection_response_languages_item import LanguageDetectionResponseLanguagesItem
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

        languages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.languages, Unset):
            languages = []
            for languages_item_data in self.languages:
                languages_item = languages_item_data.to_dict()
                languages.append(languages_item)



        primary_language = self.primary_language

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
        if languages is not UNSET:
            field_dict["languages"] = languages
        if primary_language is not UNSET:
            field_dict["primary_language"] = primary_language
        if processing_time_seconds is not UNSET:
            field_dict["processing_time_seconds"] = processing_time_seconds
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.language_detection_response_languages_item import LanguageDetectionResponseLanguagesItem
        from ..models.error_detail import ErrorDetail
        d = dict(src_dict)
        _job_id = d.pop("job_id", UNSET)
        job_id: UUID | Unset
        if isinstance(_job_id,  Unset):
            job_id = UNSET
        else:
            job_id = UUID(_job_id)




        _status = d.pop("status", UNSET)
        status: LanguageDetectionResponseStatus | Unset
        if isinstance(_status,  Unset):
            status = UNSET
        else:
            status = LanguageDetectionResponseStatus(_status)




        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _languages = d.pop("languages", UNSET)
        languages: list[LanguageDetectionResponseLanguagesItem] | Unset = UNSET
        if _languages is not UNSET:
            languages = []
            for languages_item_data in _languages:
                languages_item = LanguageDetectionResponseLanguagesItem.from_dict(languages_item_data)



                languages.append(languages_item)


        primary_language = d.pop("primary_language", UNSET)

        processing_time_seconds = d.pop("processing_time_seconds", UNSET)

        _error = d.pop("error", UNSET)
        error: ErrorDetail | Unset
        if isinstance(_error,  Unset):
            error = UNSET
        else:
            error = ErrorDetail.from_dict(_error)




        language_detection_response = cls(
            job_id=job_id,
            status=status,
            created_at=created_at,
            languages=languages,
            primary_language=primary_language,
            processing_time_seconds=processing_time_seconds,
            error=error,
        )


        language_detection_response.additional_properties = d
        return language_detection_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.transcription_response_status import TranscriptionResponseStatus
from ..types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
from uuid import UUID
import datetime

if TYPE_CHECKING:
  from ..models.error_detail import ErrorDetail
  from ..models.transcription_response_translations import TranscriptionResponseTranslations
  from ..models.transcription_response_segments_item import TranscriptionResponseSegmentsItem





T = TypeVar("T", bound="TranscriptionResponse")



@_attrs_define
class TranscriptionResponse:
    """ 
        Attributes:
            job_id (UUID | Unset): Unique job identifier for tracking
            status (TranscriptionResponseStatus | Unset): Current job status
            created_at (datetime.datetime | Unset):
            expires_at (datetime.datetime | Unset): Results expire at this timestamp (7 days default)
            language (str | Unset): Primary detected or specified language
            text (str | Unset): Full transcribed text
            segments (list[TranscriptionResponseSegmentsItem] | Unset):
            translations (TranscriptionResponseTranslations | Unset): Map of target language codes to translated text (if
                requested)
            processing_time_seconds (float | Unset): Total processing duration
            input_audio_duration_seconds (float | Unset):
            model_used (str | Unset):
            error (ErrorDetail | Unset):
            download_url (str | Unset): Blob URI for accessing results. Client should use DefaultAzureCredential to
                download.
     """

    job_id: UUID | Unset = UNSET
    status: TranscriptionResponseStatus | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    expires_at: datetime.datetime | Unset = UNSET
    language: str | Unset = UNSET
    text: str | Unset = UNSET
    segments: list[TranscriptionResponseSegmentsItem] | Unset = UNSET
    translations: TranscriptionResponseTranslations | Unset = UNSET
    processing_time_seconds: float | Unset = UNSET
    input_audio_duration_seconds: float | Unset = UNSET
    model_used: str | Unset = UNSET
    error: ErrorDetail | Unset = UNSET
    download_url: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.error_detail import ErrorDetail
        from ..models.transcription_response_translations import TranscriptionResponseTranslations
        from ..models.transcription_response_segments_item import TranscriptionResponseSegmentsItem
        job_id: str | Unset = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value


        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        expires_at: str | Unset = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        language = self.language

        text = self.text

        segments: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.segments, Unset):
            segments = []
            for segments_item_data in self.segments:
                segments_item = segments_item_data.to_dict()
                segments.append(segments_item)



        translations: dict[str, Any] | Unset = UNSET
        if not isinstance(self.translations, Unset):
            translations = self.translations.to_dict()

        processing_time_seconds = self.processing_time_seconds

        input_audio_duration_seconds = self.input_audio_duration_seconds

        model_used = self.model_used

        error: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error, Unset):
            error = self.error.to_dict()

        download_url = self.download_url


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
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if language is not UNSET:
            field_dict["language"] = language
        if text is not UNSET:
            field_dict["text"] = text
        if segments is not UNSET:
            field_dict["segments"] = segments
        if translations is not UNSET:
            field_dict["translations"] = translations
        if processing_time_seconds is not UNSET:
            field_dict["processing_time_seconds"] = processing_time_seconds
        if input_audio_duration_seconds is not UNSET:
            field_dict["input_audio_duration_seconds"] = input_audio_duration_seconds
        if model_used is not UNSET:
            field_dict["model_used"] = model_used
        if error is not UNSET:
            field_dict["error"] = error
        if download_url is not UNSET:
            field_dict["download_url"] = download_url

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_detail import ErrorDetail
        from ..models.transcription_response_translations import TranscriptionResponseTranslations
        from ..models.transcription_response_segments_item import TranscriptionResponseSegmentsItem
        d = dict(src_dict)
        _job_id = d.pop("job_id", UNSET)
        job_id: UUID | Unset
        if isinstance(_job_id,  Unset):
            job_id = UNSET
        else:
            job_id = UUID(_job_id)




        _status = d.pop("status", UNSET)
        status: TranscriptionResponseStatus | Unset
        if isinstance(_status,  Unset):
            status = UNSET
        else:
            status = TranscriptionResponseStatus(_status)




        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at,  Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)




        language = d.pop("language", UNSET)

        text = d.pop("text", UNSET)

        _segments = d.pop("segments", UNSET)
        segments: list[TranscriptionResponseSegmentsItem] | Unset = UNSET
        if _segments is not UNSET:
            segments = []
            for segments_item_data in _segments:
                segments_item = TranscriptionResponseSegmentsItem.from_dict(segments_item_data)



                segments.append(segments_item)


        _translations = d.pop("translations", UNSET)
        translations: TranscriptionResponseTranslations | Unset
        if isinstance(_translations,  Unset):
            translations = UNSET
        else:
            translations = TranscriptionResponseTranslations.from_dict(_translations)




        processing_time_seconds = d.pop("processing_time_seconds", UNSET)

        input_audio_duration_seconds = d.pop("input_audio_duration_seconds", UNSET)

        model_used = d.pop("model_used", UNSET)

        _error = d.pop("error", UNSET)
        error: ErrorDetail | Unset
        if isinstance(_error,  Unset):
            error = UNSET
        else:
            error = ErrorDetail.from_dict(_error)




        download_url = d.pop("download_url", UNSET)

        transcription_response = cls(
            job_id=job_id,
            status=status,
            created_at=created_at,
            expires_at=expires_at,
            language=language,
            text=text,
            segments=segments,
            translations=translations,
            processing_time_seconds=processing_time_seconds,
            input_audio_duration_seconds=input_audio_duration_seconds,
            model_used=model_used,
            error=error,
            download_url=download_url,
        )


        transcription_response.additional_properties = d
        return transcription_response

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

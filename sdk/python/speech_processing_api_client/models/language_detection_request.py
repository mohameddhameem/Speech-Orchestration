from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
  from ..models.audio_upload import AudioUpload
  from ..models.blob_source import BlobSource





T = TypeVar("T", bound="LanguageDetectionRequest")



@_attrs_define
class LanguageDetectionRequest:
    """ 
        Attributes:
            audio_source (AudioUpload | BlobSource):
            max_languages (int | Unset): Maximum number of detected languages to return Default: 1.
            confidence_threshold (float | Unset): Minimum confidence score for language detection Default: 0.5.
     """

    audio_source: AudioUpload | BlobSource
    max_languages: int | Unset = 1
    confidence_threshold: float | Unset = 0.5
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.audio_upload import AudioUpload
        from ..models.blob_source import BlobSource
        audio_source: dict[str, Any]
        if isinstance(self.audio_source, AudioUpload):
            audio_source = self.audio_source.to_dict()
        else:
            audio_source = self.audio_source.to_dict()


        max_languages = self.max_languages

        confidence_threshold = self.confidence_threshold


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "audio_source": audio_source,
        })
        if max_languages is not UNSET:
            field_dict["max_languages"] = max_languages
        if confidence_threshold is not UNSET:
            field_dict["confidence_threshold"] = confidence_threshold

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audio_upload import AudioUpload
        from ..models.blob_source import BlobSource
        d = dict(src_dict)
        def _parse_audio_source(data: object) -> AudioUpload | BlobSource:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                audio_source_type_0 = AudioUpload.from_dict(data)



                return audio_source_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            audio_source_type_1 = BlobSource.from_dict(data)



            return audio_source_type_1

        audio_source = _parse_audio_source(d.pop("audio_source"))


        max_languages = d.pop("max_languages", UNSET)

        confidence_threshold = d.pop("confidence_threshold", UNSET)

        language_detection_request = cls(
            audio_source=audio_source,
            max_languages=max_languages,
            confidence_threshold=confidence_threshold,
        )


        language_detection_request.additional_properties = d
        return language_detection_request

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

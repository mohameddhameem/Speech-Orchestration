from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field
import json
from .. import types

from ..types import UNSET, Unset

from ..types import File, FileTypes
from ..types import UNSET, Unset
from io import BytesIO






T = TypeVar("T", bound="DetectLanguageFilesBody")



@_attrs_define
class DetectLanguageFilesBody:
    """ 
        Attributes:
            audio_file (File):
            max_languages (int | Unset):  Default: 1.
            confidence_threshold (float | Unset):  Default: 0.5.
     """

    audio_file: File
    max_languages: int | Unset = 1
    confidence_threshold: float | Unset = 0.5
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        audio_file = self.audio_file.to_tuple()


        max_languages = self.max_languages

        confidence_threshold = self.confidence_threshold


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "audio_file": audio_file,
        })
        if max_languages is not UNSET:
            field_dict["max_languages"] = max_languages
        if confidence_threshold is not UNSET:
            field_dict["confidence_threshold"] = confidence_threshold

        return field_dict


    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("audio_file", self.audio_file.to_tuple()))



        if not isinstance(self.max_languages, Unset):
            files.append(("max_languages", (None, str(self.max_languages).encode(), "text/plain")))



        if not isinstance(self.confidence_threshold, Unset):
            files.append(("confidence_threshold", (None, str(self.confidence_threshold).encode(), "text/plain")))




        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))



        return files


    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        audio_file = File(
             payload = BytesIO(d.pop("audio_file"))
        )




        max_languages = d.pop("max_languages", UNSET)

        confidence_threshold = d.pop("confidence_threshold", UNSET)

        detect_language_files_body = cls(
            audio_file=audio_file,
            max_languages=max_languages,
            confidence_threshold=confidence_threshold,
        )


        detect_language_files_body.additional_properties = d
        return detect_language_files_body

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

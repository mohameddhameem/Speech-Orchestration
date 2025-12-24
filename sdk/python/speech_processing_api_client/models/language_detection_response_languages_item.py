from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset






T = TypeVar("T", bound="LanguageDetectionResponseLanguagesItem")



@_attrs_define
class LanguageDetectionResponseLanguagesItem:
    """ 
        Attributes:
            language (str | Unset):
            confidence (float | Unset):
            probability (float | Unset):
     """

    language: str | Unset = UNSET
    confidence: float | Unset = UNSET
    probability: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        language = self.language

        confidence = self.confidence

        probability = self.probability


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if language is not UNSET:
            field_dict["language"] = language
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if probability is not UNSET:
            field_dict["probability"] = probability

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        language = d.pop("language", UNSET)

        confidence = d.pop("confidence", UNSET)

        probability = d.pop("probability", UNSET)

        language_detection_response_languages_item = cls(
            language=language,
            confidence=confidence,
            probability=probability,
        )


        language_detection_response_languages_item.additional_properties = d
        return language_detection_response_languages_item

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

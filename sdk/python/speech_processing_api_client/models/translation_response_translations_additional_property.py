from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
  from ..models.translation_response_translations_additional_property_segments_item import TranslationResponseTranslationsAdditionalPropertySegmentsItem





T = TypeVar("T", bound="TranslationResponseTranslationsAdditionalProperty")



@_attrs_define
class TranslationResponseTranslationsAdditionalProperty:
    """ 
        Attributes:
            language (str | Unset):
            text (str | Unset):
            segments (list[TranslationResponseTranslationsAdditionalPropertySegmentsItem] | Unset):
     """

    language: str | Unset = UNSET
    text: str | Unset = UNSET
    segments: list[TranslationResponseTranslationsAdditionalPropertySegmentsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.translation_response_translations_additional_property_segments_item import TranslationResponseTranslationsAdditionalPropertySegmentsItem
        language = self.language

        text = self.text

        segments: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.segments, Unset):
            segments = []
            for segments_item_data in self.segments:
                segments_item = segments_item_data.to_dict()
                segments.append(segments_item)




        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if language is not UNSET:
            field_dict["language"] = language
        if text is not UNSET:
            field_dict["text"] = text
        if segments is not UNSET:
            field_dict["segments"] = segments

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translation_response_translations_additional_property_segments_item import TranslationResponseTranslationsAdditionalPropertySegmentsItem
        d = dict(src_dict)
        language = d.pop("language", UNSET)

        text = d.pop("text", UNSET)

        _segments = d.pop("segments", UNSET)
        segments: list[TranslationResponseTranslationsAdditionalPropertySegmentsItem] | Unset = UNSET
        if _segments is not UNSET:
            segments = []
            for segments_item_data in _segments:
                segments_item = TranslationResponseTranslationsAdditionalPropertySegmentsItem.from_dict(segments_item_data)



                segments.append(segments_item)


        translation_response_translations_additional_property = cls(
            language=language,
            text=text,
            segments=segments,
        )


        translation_response_translations_additional_property.additional_properties = d
        return translation_response_translations_additional_property

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

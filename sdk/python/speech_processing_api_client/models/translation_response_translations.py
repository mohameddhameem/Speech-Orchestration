from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
  from ..models.translation_response_translations_additional_property import TranslationResponseTranslationsAdditionalProperty





T = TypeVar("T", bound="TranslationResponseTranslations")



@_attrs_define
class TranslationResponseTranslations:
    """ Translations keyed by target language code

     """

    additional_properties: dict[str, TranslationResponseTranslationsAdditionalProperty] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.translation_response_translations_additional_property import TranslationResponseTranslationsAdditionalProperty
        
        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()


        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.translation_response_translations_additional_property import TranslationResponseTranslationsAdditionalProperty
        d = dict(src_dict)
        translation_response_translations = cls(
        )


        from ..models.translation_response_translations_additional_property_segments_item import TranslationResponseTranslationsAdditionalPropertySegmentsItem
        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = TranslationResponseTranslationsAdditionalProperty.from_dict(prop_dict)



            additional_properties[prop_name] = additional_property

        translation_response_translations.additional_properties = additional_properties
        return translation_response_translations

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> TranslationResponseTranslationsAdditionalProperty:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: TranslationResponseTranslationsAdditionalProperty) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

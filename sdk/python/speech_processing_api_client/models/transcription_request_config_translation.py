from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast






T = TypeVar("T", bound="TranscriptionRequestConfigTranslation")



@_attrs_define
class TranscriptionRequestConfigTranslation:
    """ Optional translation configuration

        Attributes:
            target_languages (list[str] | Unset):  Example: ['es-ES', 'fr-FR'].
     """

    target_languages: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        target_languages: list[str] | Unset = UNSET
        if not isinstance(self.target_languages, Unset):
            target_languages = self.target_languages




        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if target_languages is not UNSET:
            field_dict["target_languages"] = target_languages

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        target_languages = cast(list[str], d.pop("target_languages", UNSET))


        transcription_request_config_translation = cls(
            target_languages=target_languages,
        )


        transcription_request_config_translation.additional_properties = d
        return transcription_request_config_translation

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

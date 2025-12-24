from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.get_available_voices_response_200_voices_item_gender import GetAvailableVoicesResponse200VoicesItemGender
from ..types import UNSET, Unset






T = TypeVar("T", bound="GetAvailableVoicesResponse200VoicesItem")



@_attrs_define
class GetAvailableVoicesResponse200VoicesItem:
    """ 
        Attributes:
            voice_id (str | Unset):
            language (str | Unset):
            gender (GetAvailableVoicesResponse200VoicesItemGender | Unset):
            style (str | Unset): Speaking style (friendly, professional, etc.)
     """

    voice_id: str | Unset = UNSET
    language: str | Unset = UNSET
    gender: GetAvailableVoicesResponse200VoicesItemGender | Unset = UNSET
    style: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        voice_id = self.voice_id

        language = self.language

        gender: str | Unset = UNSET
        if not isinstance(self.gender, Unset):
            gender = self.gender.value


        style = self.style


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if voice_id is not UNSET:
            field_dict["voice_id"] = voice_id
        if language is not UNSET:
            field_dict["language"] = language
        if gender is not UNSET:
            field_dict["gender"] = gender
        if style is not UNSET:
            field_dict["style"] = style

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        voice_id = d.pop("voice_id", UNSET)

        language = d.pop("language", UNSET)

        _gender = d.pop("gender", UNSET)
        gender: GetAvailableVoicesResponse200VoicesItemGender | Unset
        if isinstance(_gender,  Unset):
            gender = UNSET
        else:
            gender = GetAvailableVoicesResponse200VoicesItemGender(_gender)




        style = d.pop("style", UNSET)

        get_available_voices_response_200_voices_item = cls(
            voice_id=voice_id,
            language=language,
            gender=gender,
            style=style,
        )


        get_available_voices_response_200_voices_item.additional_properties = d
        return get_available_voices_response_200_voices_item

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

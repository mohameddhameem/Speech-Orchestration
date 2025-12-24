from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
  from ..models.get_available_voices_response_200_voices_item import GetAvailableVoicesResponse200VoicesItem





T = TypeVar("T", bound="GetAvailableVoicesResponse200")



@_attrs_define
class GetAvailableVoicesResponse200:
    """ 
        Attributes:
            voices (list[GetAvailableVoicesResponse200VoicesItem] | Unset):
     """

    voices: list[GetAvailableVoicesResponse200VoicesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.get_available_voices_response_200_voices_item import GetAvailableVoicesResponse200VoicesItem
        voices: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.voices, Unset):
            voices = []
            for voices_item_data in self.voices:
                voices_item = voices_item_data.to_dict()
                voices.append(voices_item)




        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if voices is not UNSET:
            field_dict["voices"] = voices

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_available_voices_response_200_voices_item import GetAvailableVoicesResponse200VoicesItem
        d = dict(src_dict)
        _voices = d.pop("voices", UNSET)
        voices: list[GetAvailableVoicesResponse200VoicesItem] | Unset = UNSET
        if _voices is not UNSET:
            voices = []
            for voices_item_data in _voices:
                voices_item = GetAvailableVoicesResponse200VoicesItem.from_dict(voices_item_data)



                voices.append(voices_item)


        get_available_voices_response_200 = cls(
            voices=voices,
        )


        get_available_voices_response_200.additional_properties = d
        return get_available_voices_response_200

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

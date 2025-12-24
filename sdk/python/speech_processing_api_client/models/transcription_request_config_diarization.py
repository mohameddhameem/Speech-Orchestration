from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset






T = TypeVar("T", bound="TranscriptionRequestConfigDiarization")



@_attrs_define
class TranscriptionRequestConfigDiarization:
    """ 
        Attributes:
            enabled (bool | Unset):  Default: False.
            max_speakers (int | Unset):  Default: 2.
     """

    enabled: bool | Unset = False
    max_speakers: int | Unset = 2
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        max_speakers = self.max_speakers


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if max_speakers is not UNSET:
            field_dict["max_speakers"] = max_speakers

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled", UNSET)

        max_speakers = d.pop("max_speakers", UNSET)

        transcription_request_config_diarization = cls(
            enabled=enabled,
            max_speakers=max_speakers,
        )


        transcription_request_config_diarization.additional_properties = d
        return transcription_request_config_diarization

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

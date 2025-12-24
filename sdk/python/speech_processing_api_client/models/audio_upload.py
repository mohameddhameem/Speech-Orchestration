from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.audio_upload_type import AudioUploadType
from ..types import File, FileTypes
from io import BytesIO






T = TypeVar("T", bound="AudioUpload")



@_attrs_define
class AudioUpload:
    """ 
        Attributes:
            type_ (AudioUploadType): Direct file upload via multipart/form-data
            data (File): Audio file binary data (max 1GB, torch audio supported formats)
     """

    type_: AudioUploadType
    data: File
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        data = self.data.to_tuple()



        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type_,
            "data": data,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = AudioUploadType(d.pop("type"))




        data = File(
             payload = BytesIO(d.pop("data"))
        )




        audio_upload = cls(
            type_=type_,
            data=data,
        )


        audio_upload.additional_properties = d
        return audio_upload

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

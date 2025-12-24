from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.audio_blob_reference_type import AudioBlobReferenceType






T = TypeVar("T", bound="AudioBlobReference")



@_attrs_define
class AudioBlobReference:
    """ 
        Attributes:
            type_ (AudioBlobReferenceType): Reference to Azure Blob Storage file
            blob_uri (str): Full Azure Blob URI (e.g., https://account.blob.core.windows.net/container/file.wav). No SAS
                token required. Example: https://speechapi.blob.core.windows.net/audio-uploads/file.wav.
     """

    type_: AudioBlobReferenceType
    blob_uri: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        blob_uri = self.blob_uri


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type_,
            "blob_uri": blob_uri,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = AudioBlobReferenceType(d.pop("type"))




        blob_uri = d.pop("blob_uri")

        audio_blob_reference = cls(
            type_=type_,
            blob_uri=blob_uri,
        )


        audio_blob_reference.additional_properties = d
        return audio_blob_reference

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

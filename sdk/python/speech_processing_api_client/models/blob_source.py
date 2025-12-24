from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset







T = TypeVar("T", bound="BlobSource")



@_attrs_define
class BlobSource:
    """ Reference to a file in Azure Blob Storage (BYOS).

        Attributes:
            storage_account_name (str): Name of your Azure Storage Account Example: customerdata.
            container_name (str): Name of the container where audio is stored Example: audio-uploads.
            blob_name (str): Path to the specific blob Example: meetings/2024/q1_review.wav.
     """

    storage_account_name: str
    container_name: str
    blob_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        storage_account_name = self.storage_account_name

        container_name = self.container_name

        blob_name = self.blob_name


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "storage_account_name": storage_account_name,
            "container_name": container_name,
            "blob_name": blob_name,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        storage_account_name = d.pop("storage_account_name")

        container_name = d.pop("container_name")

        blob_name = d.pop("blob_name")

        blob_source = cls(
            storage_account_name=storage_account_name,
            container_name=container_name,
            blob_name=blob_name,
        )


        blob_source.additional_properties = d
        return blob_source

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

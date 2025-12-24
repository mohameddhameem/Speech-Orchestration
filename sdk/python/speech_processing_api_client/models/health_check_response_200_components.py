from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset






T = TypeVar("T", bound="HealthCheckResponse200Components")



@_attrs_define
class HealthCheckResponse200Components:
    """ 
        Attributes:
            whisper_service (str | Unset):
            azure_service (str | Unset):
            blob_storage (str | Unset):
            database (str | Unset):
     """

    whisper_service: str | Unset = UNSET
    azure_service: str | Unset = UNSET
    blob_storage: str | Unset = UNSET
    database: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        whisper_service = self.whisper_service

        azure_service = self.azure_service

        blob_storage = self.blob_storage

        database = self.database


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if whisper_service is not UNSET:
            field_dict["whisper_service"] = whisper_service
        if azure_service is not UNSET:
            field_dict["azure_service"] = azure_service
        if blob_storage is not UNSET:
            field_dict["blob_storage"] = blob_storage
        if database is not UNSET:
            field_dict["database"] = database

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        whisper_service = d.pop("whisper_service", UNSET)

        azure_service = d.pop("azure_service", UNSET)

        blob_storage = d.pop("blob_storage", UNSET)

        database = d.pop("database", UNSET)

        health_check_response_200_components = cls(
            whisper_service=whisper_service,
            azure_service=azure_service,
            blob_storage=blob_storage,
            database=database,
        )


        health_check_response_200_components.additional_properties = d
        return health_check_response_200_components

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

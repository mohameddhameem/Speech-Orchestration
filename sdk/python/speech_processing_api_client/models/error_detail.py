from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
  from ..models.error_detail_details import ErrorDetailDetails





T = TypeVar("T", bound="ErrorDetail")



@_attrs_define
class ErrorDetail:
    """ 
        Attributes:
            code (str | Unset):  Example: INVALID_AUDIO_FORMAT.
            message (str | Unset):
            details (ErrorDetailDetails | Unset):
     """

    code: str | Unset = UNSET
    message: str | Unset = UNSET
    details: ErrorDetailDetails | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.error_detail_details import ErrorDetailDetails
        code = self.code

        message = self.message

        details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.details, Unset):
            details = self.details.to_dict()


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if code is not UNSET:
            field_dict["code"] = code
        if message is not UNSET:
            field_dict["message"] = message
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_detail_details import ErrorDetailDetails
        d = dict(src_dict)
        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        _details = d.pop("details", UNSET)
        details: ErrorDetailDetails | Unset
        if isinstance(_details,  Unset):
            details = UNSET
        else:
            details = ErrorDetailDetails.from_dict(_details)




        error_detail = cls(
            code=code,
            message=message,
            details=details,
        )


        error_detail.additional_properties = d
        return error_detail

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

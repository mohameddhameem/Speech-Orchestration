from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
from uuid import UUID






T = TypeVar("T", bound="TranslationRequest")



@_attrs_define
class TranslationRequest:
    """ 
        Attributes:
            transcription_job_id (UUID): ID of completed transcription job to translate
            target_languages (list[str]): BCP-47 language codes for translation targets Example: ['es-ES', 'de-DE', 'fr-
                FR'].
            preserve_formatting (bool | Unset): Maintain original formatting in translated output Default: True.
     """

    transcription_job_id: UUID
    target_languages: list[str]
    preserve_formatting: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        transcription_job_id = str(self.transcription_job_id)

        target_languages = self.target_languages



        preserve_formatting = self.preserve_formatting


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "transcription_job_id": transcription_job_id,
            "target_languages": target_languages,
        })
        if preserve_formatting is not UNSET:
            field_dict["preserve_formatting"] = preserve_formatting

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        transcription_job_id = UUID(d.pop("transcription_job_id"))




        target_languages = cast(list[str], d.pop("target_languages"))


        preserve_formatting = d.pop("preserve_formatting", UNSET)

        translation_request = cls(
            transcription_job_id=transcription_job_id,
            target_languages=target_languages,
            preserve_formatting=preserve_formatting,
        )


        translation_request.additional_properties = d
        return translation_request

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

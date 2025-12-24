from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.transcription_request_config_model import TranscriptionRequestConfigModel
from ..models.transcription_request_config_output_format import TranscriptionRequestConfigOutputFormat
from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
  from ..models.transcription_request_config_translation import TranscriptionRequestConfigTranslation
  from ..models.transcription_request_config_diarization import TranscriptionRequestConfigDiarization





T = TypeVar("T", bound="TranscriptionRequestConfig")



@_attrs_define
class TranscriptionRequestConfig:
    """ 
        Attributes:
            language (str | Unset): BCP-47 language code. If omitted, auto-detection is performed. Example: en-US.
            model (TranscriptionRequestConfigModel | Unset):  Default: TranscriptionRequestConfigModel.WHISPER_LARGE_V3.
            output_format (TranscriptionRequestConfigOutputFormat | Unset):  Default:
                TranscriptionRequestConfigOutputFormat.JSON.
            include_timestamps (bool | Unset):  Default: False.
            diarization (TranscriptionRequestConfigDiarization | Unset):
            translation (TranscriptionRequestConfigTranslation | Unset): Optional translation configuration
            profanity_filter (bool | Unset):  Default: False.
     """

    language: str | Unset = UNSET
    model: TranscriptionRequestConfigModel | Unset = TranscriptionRequestConfigModel.WHISPER_LARGE_V3
    output_format: TranscriptionRequestConfigOutputFormat | Unset = TranscriptionRequestConfigOutputFormat.JSON
    include_timestamps: bool | Unset = False
    diarization: TranscriptionRequestConfigDiarization | Unset = UNSET
    translation: TranscriptionRequestConfigTranslation | Unset = UNSET
    profanity_filter: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.transcription_request_config_translation import TranscriptionRequestConfigTranslation
        from ..models.transcription_request_config_diarization import TranscriptionRequestConfigDiarization
        language = self.language

        model: str | Unset = UNSET
        if not isinstance(self.model, Unset):
            model = self.model.value


        output_format: str | Unset = UNSET
        if not isinstance(self.output_format, Unset):
            output_format = self.output_format.value


        include_timestamps = self.include_timestamps

        diarization: dict[str, Any] | Unset = UNSET
        if not isinstance(self.diarization, Unset):
            diarization = self.diarization.to_dict()

        translation: dict[str, Any] | Unset = UNSET
        if not isinstance(self.translation, Unset):
            translation = self.translation.to_dict()

        profanity_filter = self.profanity_filter


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if language is not UNSET:
            field_dict["language"] = language
        if model is not UNSET:
            field_dict["model"] = model
        if output_format is not UNSET:
            field_dict["output_format"] = output_format
        if include_timestamps is not UNSET:
            field_dict["include_timestamps"] = include_timestamps
        if diarization is not UNSET:
            field_dict["diarization"] = diarization
        if translation is not UNSET:
            field_dict["translation"] = translation
        if profanity_filter is not UNSET:
            field_dict["profanity_filter"] = profanity_filter

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.transcription_request_config_translation import TranscriptionRequestConfigTranslation
        from ..models.transcription_request_config_diarization import TranscriptionRequestConfigDiarization
        d = dict(src_dict)
        language = d.pop("language", UNSET)

        _model = d.pop("model", UNSET)
        model: TranscriptionRequestConfigModel | Unset
        if isinstance(_model,  Unset):
            model = UNSET
        else:
            model = TranscriptionRequestConfigModel(_model)




        _output_format = d.pop("output_format", UNSET)
        output_format: TranscriptionRequestConfigOutputFormat | Unset
        if isinstance(_output_format,  Unset):
            output_format = UNSET
        else:
            output_format = TranscriptionRequestConfigOutputFormat(_output_format)




        include_timestamps = d.pop("include_timestamps", UNSET)

        _diarization = d.pop("diarization", UNSET)
        diarization: TranscriptionRequestConfigDiarization | Unset
        if isinstance(_diarization,  Unset):
            diarization = UNSET
        else:
            diarization = TranscriptionRequestConfigDiarization.from_dict(_diarization)




        _translation = d.pop("translation", UNSET)
        translation: TranscriptionRequestConfigTranslation | Unset
        if isinstance(_translation,  Unset):
            translation = UNSET
        else:
            translation = TranscriptionRequestConfigTranslation.from_dict(_translation)




        profanity_filter = d.pop("profanity_filter", UNSET)

        transcription_request_config = cls(
            language=language,
            model=model,
            output_format=output_format,
            include_timestamps=include_timestamps,
            diarization=diarization,
            translation=translation,
            profanity_filter=profanity_filter,
        )


        transcription_request_config.additional_properties = d
        return transcription_request_config

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

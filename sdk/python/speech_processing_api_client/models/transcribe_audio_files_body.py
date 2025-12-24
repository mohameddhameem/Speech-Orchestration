from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field
import json
from .. import types

from ..types import UNSET, Unset

from ..models.transcribe_audio_files_body_model import TranscribeAudioFilesBodyModel
from ..models.transcribe_audio_files_body_output_format import TranscribeAudioFilesBodyOutputFormat
from ..types import File, FileTypes
from ..types import UNSET, Unset
from io import BytesIO






T = TypeVar("T", bound="TranscribeAudioFilesBody")



@_attrs_define
class TranscribeAudioFilesBody:
    """ 
        Attributes:
            audio_file (File): Audio file (max 1GB, torch audio formats)
            language (str):  Example: en-US.
            model (TranscribeAudioFilesBodyModel | Unset):  Default: TranscribeAudioFilesBodyModel.WHISPER_LARGE_V3.
            output_format (TranscribeAudioFilesBodyOutputFormat | Unset):  Default:
                TranscribeAudioFilesBodyOutputFormat.JSON.
            include_timestamps (bool | Unset):  Default: False.
            diarization_enabled (bool | Unset):  Default: False.
            diarization_max_speakers (int | Unset):  Default: 2.
            profanity_filter (bool | Unset):  Default: False.
            callback_url (str | Unset): Optional webhook URL for completion notification
     """

    audio_file: File
    language: str
    model: TranscribeAudioFilesBodyModel | Unset = TranscribeAudioFilesBodyModel.WHISPER_LARGE_V3
    output_format: TranscribeAudioFilesBodyOutputFormat | Unset = TranscribeAudioFilesBodyOutputFormat.JSON
    include_timestamps: bool | Unset = False
    diarization_enabled: bool | Unset = False
    diarization_max_speakers: int | Unset = 2
    profanity_filter: bool | Unset = False
    callback_url: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        audio_file = self.audio_file.to_tuple()


        language = self.language

        model: str | Unset = UNSET
        if not isinstance(self.model, Unset):
            model = self.model.value


        output_format: str | Unset = UNSET
        if not isinstance(self.output_format, Unset):
            output_format = self.output_format.value


        include_timestamps = self.include_timestamps

        diarization_enabled = self.diarization_enabled

        diarization_max_speakers = self.diarization_max_speakers

        profanity_filter = self.profanity_filter

        callback_url = self.callback_url


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "audio_file": audio_file,
            "language": language,
        })
        if model is not UNSET:
            field_dict["model"] = model
        if output_format is not UNSET:
            field_dict["output_format"] = output_format
        if include_timestamps is not UNSET:
            field_dict["include_timestamps"] = include_timestamps
        if diarization_enabled is not UNSET:
            field_dict["diarization_enabled"] = diarization_enabled
        if diarization_max_speakers is not UNSET:
            field_dict["diarization_max_speakers"] = diarization_max_speakers
        if profanity_filter is not UNSET:
            field_dict["profanity_filter"] = profanity_filter
        if callback_url is not UNSET:
            field_dict["callback_url"] = callback_url

        return field_dict


    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("audio_file", self.audio_file.to_tuple()))



        files.append(("language", (None, str(self.language).encode(), "text/plain")))



        if not isinstance(self.model, Unset):
            files.append(("model",  (None, str(self.model.value).encode(), "text/plain")))



        if not isinstance(self.output_format, Unset):
            files.append(("output_format",  (None, str(self.output_format.value).encode(), "text/plain")))



        if not isinstance(self.include_timestamps, Unset):
            files.append(("include_timestamps", (None, str(self.include_timestamps).encode(), "text/plain")))



        if not isinstance(self.diarization_enabled, Unset):
            files.append(("diarization_enabled", (None, str(self.diarization_enabled).encode(), "text/plain")))



        if not isinstance(self.diarization_max_speakers, Unset):
            files.append(("diarization_max_speakers", (None, str(self.diarization_max_speakers).encode(), "text/plain")))



        if not isinstance(self.profanity_filter, Unset):
            files.append(("profanity_filter", (None, str(self.profanity_filter).encode(), "text/plain")))



        if not isinstance(self.callback_url, Unset):
            files.append(("callback_url", (None, str(self.callback_url).encode(), "text/plain")))




        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))



        return files


    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        audio_file = File(
             payload = BytesIO(d.pop("audio_file"))
        )




        language = d.pop("language")

        _model = d.pop("model", UNSET)
        model: TranscribeAudioFilesBodyModel | Unset
        if isinstance(_model,  Unset):
            model = UNSET
        else:
            model = TranscribeAudioFilesBodyModel(_model)




        _output_format = d.pop("output_format", UNSET)
        output_format: TranscribeAudioFilesBodyOutputFormat | Unset
        if isinstance(_output_format,  Unset):
            output_format = UNSET
        else:
            output_format = TranscribeAudioFilesBodyOutputFormat(_output_format)




        include_timestamps = d.pop("include_timestamps", UNSET)

        diarization_enabled = d.pop("diarization_enabled", UNSET)

        diarization_max_speakers = d.pop("diarization_max_speakers", UNSET)

        profanity_filter = d.pop("profanity_filter", UNSET)

        callback_url = d.pop("callback_url", UNSET)

        transcribe_audio_files_body = cls(
            audio_file=audio_file,
            language=language,
            model=model,
            output_format=output_format,
            include_timestamps=include_timestamps,
            diarization_enabled=diarization_enabled,
            diarization_max_speakers=diarization_max_speakers,
            profanity_filter=profanity_filter,
            callback_url=callback_url,
        )


        transcribe_audio_files_body.additional_properties = d
        return transcribe_audio_files_body

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

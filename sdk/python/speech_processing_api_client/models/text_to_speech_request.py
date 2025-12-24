from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.text_to_speech_request_audio_format import TextToSpeechRequestAudioFormat
from ..types import UNSET, Unset






T = TypeVar("T", bound="TextToSpeechRequest")



@_attrs_define
class TextToSpeechRequest:
    """ 
        Attributes:
            text (str): Text to synthesize to speech
            language (str):  Example: en-US.
            voice_id (str): Neural voice identifier (language and region specific) Example: en-US-AriaNeural.
            speech_rate (float | Unset): Speed multiplier for speech synthesis Default: 1.0.
            pitch (float | Unset): Pitch adjustment in semitones Default: 0.0.
            audio_format (TextToSpeechRequestAudioFormat | Unset): Output audio format Default:
                TextToSpeechRequestAudioFormat.MP3.
            ssml (bool | Unset): Treat text as SSML (Speech Synthesis Markup Language) Default: False.
     """

    text: str
    language: str
    voice_id: str
    speech_rate: float | Unset = 1.0
    pitch: float | Unset = 0.0
    audio_format: TextToSpeechRequestAudioFormat | Unset = TextToSpeechRequestAudioFormat.MP3
    ssml: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        text = self.text

        language = self.language

        voice_id = self.voice_id

        speech_rate = self.speech_rate

        pitch = self.pitch

        audio_format: str | Unset = UNSET
        if not isinstance(self.audio_format, Unset):
            audio_format = self.audio_format.value


        ssml = self.ssml


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "text": text,
            "language": language,
            "voice_id": voice_id,
        })
        if speech_rate is not UNSET:
            field_dict["speech_rate"] = speech_rate
        if pitch is not UNSET:
            field_dict["pitch"] = pitch
        if audio_format is not UNSET:
            field_dict["audio_format"] = audio_format
        if ssml is not UNSET:
            field_dict["ssml"] = ssml

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        text = d.pop("text")

        language = d.pop("language")

        voice_id = d.pop("voice_id")

        speech_rate = d.pop("speech_rate", UNSET)

        pitch = d.pop("pitch", UNSET)

        _audio_format = d.pop("audio_format", UNSET)
        audio_format: TextToSpeechRequestAudioFormat | Unset
        if isinstance(_audio_format,  Unset):
            audio_format = UNSET
        else:
            audio_format = TextToSpeechRequestAudioFormat(_audio_format)




        ssml = d.pop("ssml", UNSET)

        text_to_speech_request = cls(
            text=text,
            language=language,
            voice_id=voice_id,
            speech_rate=speech_rate,
            pitch=pitch,
            audio_format=audio_format,
            ssml=ssml,
        )


        text_to_speech_request.additional_properties = d
        return text_to_speech_request

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

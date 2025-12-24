from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset






T = TypeVar("T", bound="TranscriptionResponseSegmentsItem")



@_attrs_define
class TranscriptionResponseSegmentsItem:
    """ 
        Attributes:
            start (float | Unset): Segment start time in seconds
            end (float | Unset): Segment end time in seconds
            text (str | Unset):
            speaker (str | Unset): Speaker ID if diarization enabled
            confidence (float | Unset):
     """

    start: float | Unset = UNSET
    end: float | Unset = UNSET
    text: str | Unset = UNSET
    speaker: str | Unset = UNSET
    confidence: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        start = self.start

        end = self.end

        text = self.text

        speaker = self.speaker

        confidence = self.confidence


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end
        if text is not UNSET:
            field_dict["text"] = text
        if speaker is not UNSET:
            field_dict["speaker"] = speaker
        if confidence is not UNSET:
            field_dict["confidence"] = confidence

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        start = d.pop("start", UNSET)

        end = d.pop("end", UNSET)

        text = d.pop("text", UNSET)

        speaker = d.pop("speaker", UNSET)

        confidence = d.pop("confidence", UNSET)

        transcription_response_segments_item = cls(
            start=start,
            end=end,
            text=text,
            speaker=speaker,
            confidence=confidence,
        )


        transcription_response_segments_item.additional_properties = d
        return transcription_response_segments_item

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

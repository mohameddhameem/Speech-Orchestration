from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
  from ..models.job_status_response import JobStatusResponse





T = TypeVar("T", bound="JobsList")



@_attrs_define
class JobsList:
    """ 
        Attributes:
            jobs (list[JobStatusResponse] | Unset):
            total (int | Unset):
            page (int | Unset):
            page_size (int | Unset):
            has_more (bool | Unset):
     """

    jobs: list[JobStatusResponse] | Unset = UNSET
    total: int | Unset = UNSET
    page: int | Unset = UNSET
    page_size: int | Unset = UNSET
    has_more: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.job_status_response import JobStatusResponse
        jobs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.jobs, Unset):
            jobs = []
            for jobs_item_data in self.jobs:
                jobs_item = jobs_item_data.to_dict()
                jobs.append(jobs_item)



        total = self.total

        page = self.page

        page_size = self.page_size

        has_more = self.has_more


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if jobs is not UNSET:
            field_dict["jobs"] = jobs
        if total is not UNSET:
            field_dict["total"] = total
        if page is not UNSET:
            field_dict["page"] = page
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if has_more is not UNSET:
            field_dict["has_more"] = has_more

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.job_status_response import JobStatusResponse
        d = dict(src_dict)
        _jobs = d.pop("jobs", UNSET)
        jobs: list[JobStatusResponse] | Unset = UNSET
        if _jobs is not UNSET:
            jobs = []
            for jobs_item_data in _jobs:
                jobs_item = JobStatusResponse.from_dict(jobs_item_data)



                jobs.append(jobs_item)


        total = d.pop("total", UNSET)

        page = d.pop("page", UNSET)

        page_size = d.pop("page_size", UNSET)

        has_more = d.pop("has_more", UNSET)

        jobs_list = cls(
            jobs=jobs,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )


        jobs_list.additional_properties = d
        return jobs_list

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

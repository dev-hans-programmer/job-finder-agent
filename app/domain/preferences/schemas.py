from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_WEIGHTS = {
    "skills": 40,
    "experience": 20,
    "location": 15,
    "role": 10,
    "salary": 10,
    "company": 5,
}


def _clean_values(values: list[str], field_name: str) -> list[str]:
    cleaned = [value.strip() for value in values]
    if any(not value for value in cleaned):
        raise ValueError(f"{field_name} cannot contain empty values")
    normalized = {value.casefold() for value in cleaned}
    if len(normalized) != len(cleaned):
        raise ValueError(f"{field_name} cannot contain duplicates")
    return cleaned


class Skills(BaseModel):
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)

    @field_validator("must_have", "nice_to_have")
    @classmethod
    def clean_skills(cls, values: list[str], info):
        return _clean_values(values, info.field_name)


class Locations(BaseModel):
    preferred: list[str] = Field(default_factory=list)

    @field_validator("preferred")
    @classmethod
    def clean_locations(cls, values: list[str]):
        return _clean_values(values, "preferred locations")


class Experience(BaseModel):
    min: int | None = Field(default=None, ge=0)
    max: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_range(self):
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("experience.min cannot be greater than experience.max")
        return self


class Salary(BaseModel):
    minimum_lpa: float | None = Field(default=None, ge=0)


class Companies(BaseModel):
    preferred: list[str] = Field(default_factory=list)

    @field_validator("preferred")
    @classmethod
    def clean_companies(cls, values: list[str]):
        return _clean_values(values, "preferred companies")


class Matching(BaseModel):
    minimum_score: int = Field(default=75, ge=0, le=100)


class PreferenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titles: list[str] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    locations: Locations = Field(default_factory=Locations)
    work_mode: list[str] = Field(default_factory=list)
    experience: Experience = Field(default_factory=Experience)
    salary: Salary = Field(default_factory=Salary)
    companies: Companies = Field(default_factory=Companies)
    exclusions: list[str] = Field(default_factory=list)
    matching: Matching = Field(default_factory=Matching)

    @field_validator("titles", "work_mode", "exclusions")
    @classmethod
    def clean_lists(cls, values: list[str], info):
        return _clean_values(values, info.field_name)

    @field_validator("work_mode")
    @classmethod
    def validate_work_modes(cls, values: list[str]):
        supported = {"remote", "hybrid", "onsite"}
        invalid = sorted(set(values) - supported)
        if invalid:
            raise ValueError(f"unsupported work modes: {', '.join(invalid)}")
        return values


class PreferenceResponse(PreferenceInput):
    version: int
    is_active: bool
    weights: dict[str, int]


def normalize_preferences(preferences: PreferenceInput) -> dict[str, Any]:
    return preferences.model_dump(mode="json")

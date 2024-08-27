from pydantic import BaseModel, Field
from typing import Optional, List


class JpNlpWordModel(BaseModel):
    word: Optional[str] = Field(default=None)
    normalised_form: Optional[str] = Field(default=None)
    part_of_speech: Optional[tuple] = Field(default=None)
    part_of_speech_hash: Optional[str] = Field(default=None)
    dictionary_form: Optional[str] = Field(default=None)
    is_oov: Optional[bool] = Field(default=None)
    reading_form: Optional[str] = Field(default=None)


class NovelTextProcessingSentence(BaseModel):
    sentence: str
    line_number: Optional[int] = Field(default=None)
    lenght: Optional[int] = Field(default=None)


class TokenizedNormalizedSentence(BaseModel):
    sentence: str
    all_tokens_count: Optional[int] = Field(default=0)
    tokens_passed: Optional[List[JpNlpWordModel]] = Field(default=[])
    ignored: Optional[List[JpNlpWordModel]] = Field(default=[])
    on_hold: Optional[List[JpNlpWordModel]] = Field(default=[])
    pos_blacklisted: Optional[List[JpNlpWordModel]] = Field(default=[])
    not_passed: Optional[List[JpNlpWordModel]] = Field(default=[])
    all_tokens: Optional[List[JpNlpWordModel]] = Field(default=[])


class MiaDbCardtemplate(BaseModel):
    sentence: str
    meaning: Optional[str] = Field(default="")
    audio: Optional[str] = Field(default="")
    screen: Optional[str] = Field(default="")
    unknown_word: str
    card_id: str
    tags: Optional[str] = Field(default="")
    context: Optional[str] = Field(default="")

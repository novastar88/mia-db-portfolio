from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class CardModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    deck: Optional[str] = Field(default=None)
    creation_time: Optional[datetime] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    note_type: Optional[str] = Field(default=None)
    sentence: str
    audio: Optional[str] = Field(default=None)
    screen: Optional[str] = Field(default=None)
    meaning: Optional[str] = Field(default=None)
    updated_time: Optional[datetime] = Field(default=None)
    line_number: Optional[int] = Field(default=None)
    ai_interpretation: Optional[str] = Field(default=None)


class AnkiStatusModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    status: Optional[int] = Field(default=None)
    creation_time: Optional[datetime] = Field(default=None)
    card_id: Optional[int] = Field(default=None)
    details: Optional[str] = Field(default=None)
    handled: Optional[bool] = Field(default=None)
    updated_time: Optional[datetime] = Field(default=None)


class RecalcModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    result: Optional[int] = Field(default=None)
    unknown_word: Optional[str] = Field(default=None)
    time_checked: Optional[datetime] = Field(default=None)
    card_id: Optional[int] = Field(default=None)
    rating: Optional[int] = Field(default=None)


class DeckModel(BaseModel):
    deck_name: str
    creation_time: datetime


class NoteTypeModel(BaseModel):
    note_name: Optional[str] = Field(default=None)
    language: Optional[Literal["jp", "eng"]] = Field(default=None)
    creation_time: Optional[datetime] = Field(default=None)
    bonus_rating_note: Optional[int] = Field(default=None)


class PreprocessingModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    all_words: List[str]
    words_number: Optional[int] = Field(default=None)
    processed_time: Optional[datetime] = Field(default=None)
    related_card: int
    bonus_rating_sum_a: Optional[int] = Field(default=None)


class PriorityWordsListModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    name: Optional[str] = Field(default=None)
    lang: Optional[str] = Field(default=None)
    words: List[str]
    updated_time: Optional[datetime] = Field(default=None)
    creation_time: Optional[datetime] = Field(default=None)


class FrequencyWordsListModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    namee: str
    lang: str
    words: List[str]
    updated_time: Optional[datetime] = Field(default=None)
    creation_time: Optional[datetime] = Field(default=None)


class WordsKnown(BaseModel):
    idd: Optional[int] = Field(default=None)
    word: str
    time_known: Optional[datetime] = Field(default=None)
    lang: Optional[str] = Field(default=None)


class WordsIgnoreModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    lang: Optional[str] = Field(default=None)
    time_added: Optional[datetime] = Field(default=None)
    word: str


class WordsOnHoldModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    lang: Optional[str] = Field(default=None)
    time_added: Optional[datetime] = Field(default=None)
    word: str


class JpPosBlacklistModel(BaseModel):
    idd: Optional[int] = Field(default=None)
    time_added: Optional[datetime] = Field(default=None)
    pos_hash: str


class FullTextsStorage(BaseModel):
    idd: Optional[int] = Field(default=None)
    lang: Optional[str] = Field(default=None)
    file_path: Optional[str] = Field(default=None)
    file_name: Optional[str] = Field(default=None)
    sentences: List[str]
    sentences_hash: Optional[str] = Field(default=None)
    time_added: Optional[datetime] = Field(default=None)

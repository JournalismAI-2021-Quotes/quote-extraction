class Quote:
    def __init__(self, quote_text: str, speaker: str = None, quote_text_optional_second_part: str = None,
                 cue: str = None, additional_cue: str = None, quote_text_optional_third_part:str = None):
        self.quote_text = quote_text
        self.speaker = speaker
        self.quote_text_optional_second_part = quote_text_optional_second_part
        self.cue = cue
        self.additional_cue = additional_cue
        self.quote_text_optional_third_part = quote_text_optional_third_part
        self._QUOTE_TYPE = None


    @property
    def QUOTE_TYPE(self):
        return self._QUOTE_TYPE

    @QUOTE_TYPE.setter
    def QUOTE_TYPE(self, value: int):
        self._QUOTE_TYPE = value

    def __repr__(self):
        return str({"quote_text": self.quote_text,
                    "speaker": self.speaker,
                    "quote_text_optional_second_part": self.quote_text_optional_second_part,
                    "cue": self.cue,
                    "additional_cue": self.additional_cue,
                    "quote_text_optional_third_part": self.quote_text_optional_third_part,
                    "QUOTE_TYPE": self.QUOTE_TYPE})

    def to_dict(self):
        return {"quote_text": self.quote_text,
                "speaker": self.speaker,
                "quote_text_optional_second_part": self.quote_text_optional_second_part,
                "cue": self.cue,
                "additional_cue": self.additional_cue,
                "quote_text_optional_third_part": self.quote_text_optional_third_part,
                "QUOTE_TYPE": self.QUOTE_TYPE}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all([self.quote_text == other.quote_text,
                        self.speaker == other.speaker,
                        self.quote_text_optional_second_part == other.quote_text_optional_second_part,
                        self.cue == other.cue])
        else:
            return False

    def __hash__(self):
        if self.quote_text_optional_second_part is None:
            return hash(f"{self.quote_text} {self.speaker} {self.cue}")
        else:
            return hash(f"{self.quote_text} {self.speaker} {self.cue} {self.quote_text_optional_second_part}")

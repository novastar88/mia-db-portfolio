import deepl
from utilities import config_reader


class Translator:
    '''JA, PL, EN'''

    def __init__(self, input_lang: str, output_lang: str) -> None:
        auth = config_reader()["deepl"]["api_key"]
        self.translator = deepl.Translator(auth, skip_language_check=True)
        self.input_lang = input_lang
        self.output_lang = output_lang

    def translate_sentence(self, inpt: str):
        return self.translator.translate_text(inpt, source_lang=self.input_lang, target_lang=self.output_lang).text

WHITE_SPACES = [r" ", r"　", r"\u3000"]
BREAKERS = [r"\n", r"\t"]
LINE_END = [r"。", r".", r"？", r"──"]
THRASH_CHARS = [r"&ensp;", r"<br />",
                r"<div>", r"</div>", r"◆", r"&lrm;"]
IGNORE_EXPRESSIONS = THRASH_CHARS + BREAKERS + WHITE_SPACES
# IGNORE_IN_DEFINITIONS = [r"→.*.", r"⇀く.*.", r"\n$"] + IGNORE_EXPRESSIONS
# IGNORE_IN_DEFINITIONS_EXPORT = [r"→.*.", r"⇀く.*.", r"\n$", r"^\n"]
JP_REGEX = r"[\u3041-\u3096]|[\u30A0-\u30FF]|[\u3400-\u4DB5]|[\u4E00-\u9FCB]|[\u2E80-\u2FD5]|[\uFF5F-\uFF9F]|[\u31F0-\u31FF\u3220-\u3243\u3280-\u337F]"
KATAKANA_HIRAGANA = r"[\u3041-\u3096]|[\u30A0-\u30FF]"
KANA_REGEX = r"(\[.*?\])"
ENCODINGS = [r"utf-8", r"shift_jis",
             r"shift_jis_2004", r"shift_jisx0213", r"utf_16"]
EMPTY_LINE = WHITE_SPACES + BREAKERS + LINE_END

JP_SENTENCES_SPLITTER_PATTERN = r"^\s*(.*)\s*$"

# zdanie dokładny regex 90-99%
# r"^[。,？,\s]*([「,〝]*.*[。,？,〟,」,──])\s*$"

FILE_DATE_FORMAT = "%d%m%Y_%H%M%S"
FILE_DATE_FORMAT_PREC = "%d%m%Y_%H%M%S%f"

"""Pronunciation guides (romanization) for transcripts in non-Latin scripts.

A Whisper transcript of Chinese, Japanese, Korean, Russian, Greek, Hebrew,
Arabic or Hindi is unreadable to someone who does not know the script, even
though the transcription itself is correct. This module produces a reading
for each word so the frontend can render it as ruby text above the original:

    你好          日本語         Привет
    nǐ hǎo        nihongo        Privet

Like everything else here it runs entirely offline: `pypinyin` and `pykakasi`
ship their dictionaries in the wheel, and every other script is handled by the
transliteration tables below. No API key and no network call.

Output shape (`romanize_transcript`):

    lines = [
      [ {"t": "你", "r": "nǐ"}, {"t": "好", "r": "hǎo"}, {"t": "，"} ],
      ...
    ]

Each token is one span of the transcript. `r` is present only when there is a
reading to show above it; plain runs (spaces, Latin text, punctuation,
timestamps) are emitted verbatim with no `r` so the frontend renders them as-is.
"""

import re
import unicodedata

# Optional engines. Missing ones simply disable that language rather than
# breaking transcription, so an old virtualenv still serves the site.
try:
    from pypinyin import Style, pinyin as _pypinyin
except ImportError:  # pragma: no cover - depends on the install
    _pypinyin = None

try:
    import pykakasi

    _kakasi = pykakasi.kakasi()
except ImportError:  # pragma: no cover - depends on the install
    _kakasi = None


# Name of the romanization system, shown in the UI next to the toggle.
SYSTEM_NAMES = {
    "zh": "Pinyin",
    "ja": "Romaji",
    "ko": "Revised Romanization",
    "ru": "Transliteration",
    "uk": "Transliteration",
    "bg": "Transliteration",
    "el": "Transliteration",
    "he": "Transliteration",
    "ar": "Transliteration",
    "fa": "Transliteration",
    "ur": "Transliteration",
    "hi": "Transliteration",
}

# Scripts we can read out loud. Thai, Tamil, Telugu, Bengali and Malayalam are
# deliberately absent: a character-by-character mapping of those scripts
# produces misleading output (Thai writes some vowels before the consonant they
# follow), and shipping a wrong pronunciation is worse than shipping none.
# Adding one is a matter of adding a table plus a branch in `_romanize_word`.


def _script_of(ch: str) -> str | None:
    """Which writing system a character belongs to, or None for Latin/punctuation."""
    o = ord(ch)
    if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0xF900 <= o <= 0xFAFF:
        return "han"
    if 0x3040 <= o <= 0x30FF or 0x31F0 <= o <= 0x31FF:
        return "kana"
    if 0xAC00 <= o <= 0xD7A3 or 0x1100 <= o <= 0x11FF or 0x3130 <= o <= 0x318F:
        return "hangul"
    if 0x0400 <= o <= 0x052F:
        return "cyrillic"
    if 0x0370 <= o <= 0x03FF or 0x1F00 <= o <= 0x1FFF:
        return "greek"
    if 0x0590 <= o <= 0x05FF or 0xFB1D <= o <= 0xFB4F:
        return "hebrew"
    if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0xFB50 <= o <= 0xFEFF:
        return "arabic"
    if 0x0900 <= o <= 0x097F:
        return "devanagari"
    return None


# --------------------------------------------------------------------------
# Korean - Revised Romanization of Hangul
# --------------------------------------------------------------------------

_HANGUL_BASE = 0xAC00
_ONSETS = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "",
           "j", "jj", "ch", "k", "t", "p", "h"]
_NUCLEI = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae",
           "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
# Coda as pronounced at the end of a syllable.
_CODAS = ["", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "p", "l",
          "l", "p", "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t",
          "p", "t"]
# Coda as pronounced when it slides onto a following vowel (liaison).
# Index 27 is a final hieut, which goes silent before a vowel rather than
# carrying over: 좋아요 is joayo, not johayo.
_CODA_ONSETS = ["", "g", "kk", "ks", "n", "nj", "nh", "d", "r", "lg", "lm",
                "lb", "ls", "lt", "lp", "lh", "m", "b", "bs", "s", "ss", "ng",
                "j", "ch", "k", "t", "p", ""]
_SILENT_ONSET = 11  # ieung, the placeholder consonant


def _romanize_hangul(word: str) -> list[tuple[str, str]]:
    """Romanize a run of Hangul, one reading per syllable block.

    Applies the liaison rule (a final consonant moves onto a following
    silent-onset syllable), so 한국어 reads han-gu-geo rather than han-guk-eo.
    """
    parts = []
    for ch in word:
        code = ord(ch) - _HANGUL_BASE
        if 0 <= code < 11172:
            parts.append([code // 588, (code % 588) // 28, code % 28])
        else:
            parts.append(None)

    out: list[tuple[str, str]] = []
    carried = ""
    for i, ch in enumerate(word):
        jamo = parts[i]
        if jamo is None:
            out.append((ch, carried + ch))
            carried = ""
            continue
        onset, nucleus, coda = jamo
        nxt = parts[i + 1] if i + 1 < len(parts) else None
        # A carried consonant lands on this syllable's silent onset.
        head = carried + _ONSETS[onset]
        carried = ""
        if coda and nxt is not None and nxt[0] == _SILENT_ONSET:
            # The final consonant is pronounced as the next syllable's onset.
            carried = _CODA_ONSETS[coda]
            tail = ""
        else:
            tail = _CODAS[coda]
        out.append((ch, head + _NUCLEI[nucleus] + tail))
    return out


# --------------------------------------------------------------------------
# Alphabetic scripts - table driven
# --------------------------------------------------------------------------

_CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    # Ukrainian and Belarusian
    "і": "i", "ї": "yi", "є": "ye", "ґ": "g", "ў": "w",
    # Serbian and Macedonian
    "ђ": "dj", "ј": "j", "љ": "lj", "њ": "nj", "ћ": "c", "џ": "dz",
    "ѓ": "gj", "ќ": "kj", "ѕ": "dz",
}

_GREEK = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i",
    "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x",
    "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y",
    "φ": "f", "χ": "ch", "ψ": "ps", "ω": "o",
    "ά": "a", "έ": "e", "ή": "i", "ί": "i", "ό": "o", "ύ": "y", "ώ": "o",
    "ϊ": "i", "ϋ": "y", "ΐ": "i", "ΰ": "y",
}
# Greek digraphs carry sounds no single letter does; check these first.
_GREEK_PAIRS = {
    "μπ": "b", "ντ": "d", "γκ": "g", "γγ": "ng", "τσ": "ts", "τζ": "tz",
    "ου": "ou", "ού": "ou", "αι": "e", "αί": "e", "ει": "i", "εί": "i",
    "οι": "i", "οί": "i", "αυ": "av", "αύ": "av", "ευ": "ev", "εύ": "ev",
}

_HEBREW = {
    "א": "", "ב": "v", "ג": "g", "ד": "d", "ה": "h", "ו": "v", "ז": "z",
    "ח": "ch", "ט": "t", "י": "y", "כ": "kh", "ך": "kh", "ל": "l", "מ": "m",
    "ם": "m", "נ": "n", "ן": "n", "ס": "s", "ע": "", "פ": "f", "ף": "f",
    "צ": "ts", "ץ": "ts", "ק": "k", "ר": "r", "ש": "sh", "ת": "t",
}
# A dagesh (dot) hardens these three letters.
_HEBREW_DAGESH = {"ב": "b", "כ": "k", "ך": "k", "פ": "p", "ף": "p"}
_HEBREW_NIQQUD = {
    "ְ": "", "ֱ": "e", "ֲ": "a", "ֳ": "o", "ִ": "i",
    "ֵ": "e", "ֶ": "e", "ַ": "a", "ָ": "a", "ֹ": "o",
    "ֻ": "u",
}
_DAGESH = "ּ"

_ARABIC = {
    "ا": "a", "أ": "a", "إ": "i", "آ": "aa", "ٱ": "a", "ب": "b", "ت": "t",
    "ث": "th", "ج": "j", "ح": "h", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r",
    "ز": "z", "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t", "ظ": "z",
    "ع": "'", "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m",
    "ن": "n", "ه": "h", "و": "w", "ي": "y", "ى": "a", "ة": "h", "ء": "'",
    "ئ": "'", "ؤ": "'",
    # Persian
    "پ": "p", "چ": "ch", "ژ": "zh", "گ": "g", "ک": "k", "ی": "y",
    # Urdu
    "ٹ": "t", "ڈ": "d", "ڑ": "r", "ں": "n", "ھ": "h", "ے": "e", "ہ": "h",
    # Short vowels, when the text is vocalized
    "َ": "a", "ِ": "i", "ُ": "u", "ً": "an",
    "ٍ": "in", "ٌ": "un", "ْ": "",
}
_SHADDA = "ّ"  # doubles the preceding consonant

_DEVA_VOWELS = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ii", "उ": "u", "ऊ": "uu",
    "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऑ": "o",
}
_DEVA_CONS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng", "च": "ch",
    "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny", "ट": "t", "ठ": "th",
    "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d",
    "ध": "dh", "न": "n", "प": "p", "फ": "ph", "ब": "b", "भ": "bh",
    "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h", "ळ": "l",
    "क़": "q", "ख़": "kh", "ग़": "gh", "ज़": "z", "ड़": "r", "ढ़": "rh", "फ़": "f",
}
_DEVA_MATRA = {
    "ा": "aa", "ि": "i", "ी": "ii", "ु": "u", "ू": "uu", "ृ": "ri",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ॉ": "o", "ॅ": "e",
}
_DEVA_SIGNS = {"ं": "n", "ँ": "n", "ः": "h", "़": ""}
_VIRAMA = "्"


def _map_table(word: str, table: dict[str, str]) -> str:
    return "".join(table.get(ch, table.get(ch.lower(), ch)) for ch in word)


def _translit_greek(word: str) -> str:
    out, i = [], 0
    low = word.lower()
    while i < len(low):
        pair = low[i:i + 2]
        if pair in _GREEK_PAIRS:
            out.append(_GREEK_PAIRS[pair])
            i += 2
            continue
        out.append(_GREEK.get(low[i], low[i]))
        i += 1
    return "".join(out)


def _translit_hebrew(word: str) -> str:
    out, i = [], 0
    while i < len(word):
        ch = word[i]
        nxt = word[i + 1] if i + 1 < len(word) else ""
        if ch in _HEBREW_NIQQUD:
            out.append(_HEBREW_NIQQUD[ch])
        elif nxt == _DAGESH and ch in _HEBREW_DAGESH:
            out.append(_HEBREW_DAGESH[ch])
            i += 1
        elif ch == _DAGESH:
            pass
        else:
            out.append(_HEBREW.get(ch, ch))
        i += 1
    return "".join(out)


def _translit_arabic(word: str) -> str:
    out = []
    for ch in word:
        if ch == _SHADDA:
            if out:
                out.append(out[-1])
            continue
        out.append(_ARABIC.get(ch, ""))
    return "".join(out)


def _translit_devanagari(word: str) -> str:
    """Devanagari is an abugida: a bare consonant carries an inherent 'a'."""
    out, i = [], 0
    while i < len(word):
        ch = word[i]
        if ch in _DEVA_CONS:
            out.append(_DEVA_CONS[ch])
            nxt = word[i + 1] if i + 1 < len(word) else ""
            if nxt == _VIRAMA:
                i += 2  # conjunct: the inherent vowel is suppressed
                continue
            if nxt in _DEVA_MATRA:
                out.append(_DEVA_MATRA[nxt])
                i += 2
                continue
            out.append("a")
        elif ch in _DEVA_VOWELS:
            out.append(_DEVA_VOWELS[ch])
        elif ch in _DEVA_SIGNS:
            out.append(_DEVA_SIGNS[ch])
        elif ch in _DEVA_MATRA:
            out.append(_DEVA_MATRA[ch])
        i += 1
    return "".join(out)


def _restore_case(original: str, reading: str) -> str:
    """Keep a capitalized source word capitalized in its reading."""
    if not reading or not original:
        return reading
    first = next((c for c in original if c.isalpha()), "")
    if first and first.isupper():
        return reading[0].upper() + reading[1:]
    return reading


def _romanize_word(word: str, script: str) -> str:
    if script == "cyrillic":
        return _restore_case(word, _map_table(word.lower(), _CYRILLIC))
    if script == "greek":
        return _restore_case(word, _translit_greek(word))
    if script == "hebrew":
        return _translit_hebrew(word)
    if script == "arabic":
        return _translit_arabic(word)
    if script == "devanagari":
        return _translit_devanagari(word)
    return ""


# --------------------------------------------------------------------------
# Tokenizing a line into annotated and plain spans
# --------------------------------------------------------------------------

_WORD_SCRIPTS = {"cyrillic", "greek", "hebrew", "arabic", "devanagari"}


def _tokens_for_line(line: str, lang: str) -> list[dict]:
    """Split one line into tokens, attaching a reading wherever we have one."""
    if lang == "ja" or _contains_kana(line):
        return _tokens_japanese(line)

    tokens: list[dict] = []
    plain: list[str] = []

    def flush():
        if plain:
            tokens.append({"t": "".join(plain)})
            plain.clear()

    i = 0
    while i < len(line):
        ch = line[i]
        script = _script_of(ch)

        if script == "han" and _pypinyin is not None:
            run = _take_run(line, i, "han")
            flush()
            readings = _pypinyin(run, style=Style.TONE, errors="ignore")
            # One reading per character keeps the ruby aligned above its hanzi.
            for idx, hanzi in enumerate(run):
                reading = readings[idx][0] if idx < len(readings) else ""
                tokens.append({"t": hanzi, "r": reading} if reading else {"t": hanzi})
            i += len(run)
            continue

        if script == "hangul":
            run = _take_run(line, i, "hangul")
            flush()
            for syllable, reading in _romanize_hangul(run):
                tokens.append({"t": syllable, "r": reading} if reading else {"t": syllable})
            i += len(run)
            continue

        if script in _WORD_SCRIPTS:
            run = _take_run(line, i, script)
            flush()
            reading = _romanize_word(run, script).strip()
            tokens.append({"t": run, "r": reading} if reading else {"t": run})
            i += len(run)
            continue

        plain.append(ch)
        i += 1

    flush()
    return tokens


def _take_run(line: str, start: int, script: str) -> str:
    """Longest span from `start` that stays in one script (combining marks included)."""
    end = start
    while end < len(line):
        ch = line[end]
        if _script_of(ch) == script or (end > start and unicodedata.combining(ch)):
            end += 1
        else:
            break
    return line[start:end]


def _contains_kana(text: str) -> bool:
    return any(_script_of(c) == "kana" for c in text)


def _tokens_japanese(line: str) -> list[dict]:
    """Japanese needs a real morphological pass: kanji readings depend on context."""
    if _kakasi is None:
        return [{"t": line}]
    tokens: list[dict] = []
    for chunk in _kakasi.convert(line):
        original = chunk.get("orig", "")
        if not original:
            continue
        reading = (chunk.get("hepburn") or "").strip()
        # Only annotate spans actually written in Japanese script; the converter
        # also hands back Latin words and punctuation unchanged.
        needs_reading = any(_script_of(c) in ("han", "kana") for c in original)
        if needs_reading and reading and reading.lower() != original.lower():
            tokens.append({"t": original, "r": reading})
        else:
            tokens.append({"t": original})
    return tokens


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def is_supported(lang: str, text: str = "") -> bool:
    """True when we can produce a pronunciation guide for this transcript."""
    if lang == "zh" and _pypinyin is None:
        return False
    if lang == "ja" and _kakasi is None:
        return False
    if lang in SYSTEM_NAMES:
        return True
    # Fall back to sniffing the text, so a mislabeled language still gets help.
    return any(_script_of(c) is not None for c in text)


def system_name(lang: str, text: str = "") -> str:
    if lang in SYSTEM_NAMES:
        return SYSTEM_NAMES[lang]
    scripts = {_script_of(c) for c in text} - {None}
    if "kana" in scripts:
        return "Romaji"
    if "hangul" in scripts:
        return "Revised Romanization"
    if "han" in scripts:
        return "Pinyin"
    return "Transliteration"


def romanize_transcript(text: str, lang: str) -> tuple[list[list[dict]] | None, str | None]:
    """Annotate a transcript with readings, line by line.

    Returns `(lines, system)` where `lines` mirrors the transcript's own line
    structure, or `(None, None)` when the transcript is already in Latin script
    and needs no help.
    """
    if not text or not is_supported(lang, text):
        return None, None

    lines = [_tokens_for_line(line, lang) for line in text.split("\n")]
    # If nothing picked up a reading the transcript was Latin all along; say so
    # rather than handing the UI a toggle that does nothing.
    if not any(tok.get("r") for line in lines for tok in line):
        return None, None
    return lines, system_name(lang, text)


def to_interleaved_text(lines: list[list[dict]]) -> str:
    """Flatten annotated lines to plain text: each line followed by its reading.

    Used for copy and download, where ruby markup cannot survive.
    """
    out: list[str] = []
    for line in lines:
        original = "".join(tok["t"] for tok in line)
        if not original.strip():
            out.append("")
            continue
        out.append(original)
        if any(tok.get("r") for tok in line):
            reading = " ".join(
                tok["r"] if tok.get("r") else tok["t"].strip()
                for tok in line
                if tok.get("r") or tok["t"].strip()
            )
            out.append(re.sub(r"\s+", " ", reading).strip())
    return "\n".join(out)

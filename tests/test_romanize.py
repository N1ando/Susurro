"""Tests for the pronunciation guide.

These are the highest-value tests in the project: `romanize` is pure, has no
model dependency, and is where a silent regression would be least visible - a
wrong reading still renders as perfectly plausible text.
"""

import unicodedata

import pytest

import romanize


# --------------------------------------------------------------------------
# Chinese - pypinyin, one reading per character
# --------------------------------------------------------------------------

class TestChinese:
    def test_hanzi_get_pinyin_with_tone_marks(self):
        lines, system = romanize.romanize_transcript("你好", "zh")
        assert system == "Pinyin"
        assert [(t["t"], t["r"]) for t in lines[0]] == [("你", "nǐ"), ("好", "hǎo")]

    def test_one_token_per_character_so_ruby_stays_aligned(self):
        lines, _ = romanize.romanize_transcript("你好世界", "zh")
        assert [t["t"] for t in lines[0]] == ["你", "好", "世", "界"]
        assert all(t["r"] for t in lines[0])

    def test_latin_and_punctuation_are_left_unannotated(self):
        lines, _ = romanize.romanize_transcript("你好，world", "zh")
        annotated = [t for t in lines[0] if t.get("r")]
        plain = [t for t in lines[0] if not t.get("r")]
        assert [t["t"] for t in annotated] == ["你", "好"]
        assert [t["t"] for t in plain] == ["，world"]

    def test_timestamp_prefix_passes_through_as_plain_text(self):
        lines, _ = romanize.romanize_transcript("[00:03] 你好", "zh")
        assert lines[0][0] == {"t": "[00:03] "}


# --------------------------------------------------------------------------
# Japanese - pykakasi, per word (kanji readings are context-dependent)
# --------------------------------------------------------------------------

class TestJapanese:
    def test_kanji_compound_reads_as_one_word(self):
        lines, system = romanize.romanize_transcript("日本語", "ja")
        assert system == "Romaji"
        assert [(t["t"], t["r"]) for t in lines[0]] == [("日本語", "nihongo")]

    def test_mixed_kanji_and_kana_split_into_words(self):
        lines, _ = romanize.romanize_transcript("東京へ行きます", "ja")
        assert [(t["t"], t.get("r")) for t in lines[0]] == [
            ("東京", "toukyou"), ("へ", "he"), ("行き", "iki"), ("ます", "masu"),
        ]

    def test_kana_is_detected_even_when_language_is_wrong(self):
        # Whisper occasionally mislabels; kana in the text should still route
        # to the Japanese engine rather than being read as Chinese.
        lines, _ = romanize.romanize_transcript("ひらがな", "zh")
        assert lines[0][0]["r"] == "hiragana"


# --------------------------------------------------------------------------
# Korean - Revised Romanization, built in
# --------------------------------------------------------------------------

class TestKorean:
    def test_liaison_moves_a_final_consonant_onto_the_next_syllable(self):
        # The whole point of the rule: naive per-syllable output would be
        # han-guk-eo, which is not how the word is pronounced.
        lines, system = romanize.romanize_transcript("한국어", "ko")
        assert system == "Revised Romanization"
        assert [t["r"] for t in lines[0]] == ["han", "gu", "geo"]

    def test_no_liaison_when_the_next_syllable_has_a_real_onset(self):
        lines, _ = romanize.romanize_transcript("한글", "ko")
        assert [t["r"] for t in lines[0]] == ["han", "geul"]

    def test_final_hieut_goes_silent_before_a_vowel(self):
        # Regression: a final hieut must not carry over as an 'h'.
        lines, _ = romanize.romanize_transcript("좋아요", "ko")
        assert [t["r"] for t in lines[0]] == ["jo", "a", "yo"]

    def test_each_syllable_block_is_its_own_token(self):
        lines, _ = romanize.romanize_transcript("한국어를", "ko")
        assert [t["t"] for t in lines[0]] == ["한", "국", "어", "를"]


# --------------------------------------------------------------------------
# Alphabetic scripts - table driven, annotated per word
# --------------------------------------------------------------------------

class TestCyrillic:
    def test_word_level_reading_and_capitalization_is_kept(self):
        lines, system = romanize.romanize_transcript("Привет мир", "ru")
        assert system == "Transliteration"
        assert [(t["t"], t.get("r")) for t in lines[0]] == [
            ("Привет", "Privet"), (" ", None), ("мир", "mir"),
        ]

    def test_ukrainian_letters_outside_the_russian_alphabet(self):
        lines, _ = romanize.romanize_transcript("Київ", "uk")
        assert lines[0][0]["r"] == "Kiyiv"


class TestGreek:
    def test_digraph_beats_letter_by_letter(self):
        # mu+pi is a single /b/ sound; mapping each letter gives "mp".
        lines, _ = romanize.romanize_transcript("μπύρα", "el")
        assert lines[0][0]["r"] == "byra"

    def test_accented_vowels_are_handled(self):
        lines, _ = romanize.romanize_transcript("Καλημέρα", "el")
        assert lines[0][0]["r"] == "Kalimera"


class TestHebrew:
    def test_dagesh_hardens_the_letter(self):
        lines, _ = romanize.romanize_transcript("בּית", "he")
        assert lines[0][0]["r"] == "byt"  # bet with dagesh reads b, not v

    def test_unvocalized_text_yields_consonants_only(self):
        # Documented limitation: short vowels are not written in the source,
        # so they cannot appear in the reading.
        lines, _ = romanize.romanize_transcript("שלום", "he")
        assert lines[0][0]["r"] == "shlvm"


class TestArabic:
    def test_unvocalized_text_yields_consonants_only(self):
        lines, _ = romanize.romanize_transcript("مرحبا", "ar")
        assert lines[0][0]["r"] == "mrhba"

    def test_shadda_doubles_the_preceding_consonant(self):
        plain, _ = romanize.romanize_transcript("مدرسة", "ar")
        with_shadda, _ = romanize.romanize_transcript("مدرّسة", "ar")
        assert len(with_shadda[0][0]["r"]) == len(plain[0][0]["r"]) + 1


class TestDevanagari:
    def test_inherent_vowel_and_virama(self):
        # A bare consonant carries an 'a'; the virama suppresses it.
        lines, _ = romanize.romanize_transcript("नमस्ते", "hi")
        assert lines[0][0]["r"] == "namaste"

    def test_vowel_signs_replace_the_inherent_vowel(self):
        lines, _ = romanize.romanize_transcript("हिन्दी", "hi")
        assert lines[0][0]["r"] == "hindii"


# --------------------------------------------------------------------------
# When there is nothing to add
# --------------------------------------------------------------------------

class TestNoRomanization:
    @pytest.mark.parametrize("text,lang", [
        ("Hello world", "en"),
        ("Bonjour tout le monde", "fr"),
        ("", "zh"),
        ("   ", "zh"),
        ("12:30", "en"),
    ])
    def test_latin_and_empty_transcripts_get_no_guide(self, text, lang):
        assert romanize.romanize_transcript(text, lang) == (None, None)

    @pytest.mark.parametrize("text,lang", [
        ("สวัสดี", "th"),      # Thai
        ("வணக்கம்", "ta"),      # Tamil
    ])
    def test_deliberately_unsupported_scripts_return_nothing(self, text, lang):
        # These are excluded on purpose: a character-by-character mapping of
        # them is misleading, and no guide beats a wrong guide.
        assert romanize.romanize_transcript(text, lang) == (None, None)

    def test_is_supported_reflects_the_script_not_just_the_language_code(self):
        assert romanize.is_supported("zh", "你好") is True
        assert romanize.is_supported("en", "Hello") is False


# --------------------------------------------------------------------------
# Structural invariants that must hold for every script
# --------------------------------------------------------------------------

SCRIPT_SAMPLES = [
    ("你好世界，这是测试。", "zh"),
    ("日本語を勉強しています。", "ja"),
    ("한국어를 배우고 있어요.", "ko"),
    ("Привет, как дела?", "ru"),
    ("Καλημέρα κόσμε!", "el"),
    ("שלום עולם", "he"),
    ("مرحبا بالعالم", "ar"),
    ("नमस्ते दुनिया", "hi"),
]


class TestInvariants:
    @pytest.mark.parametrize("text,lang", SCRIPT_SAMPLES)
    def test_tokens_reassemble_into_the_original_line(self, text, lang):
        # The frontend renders tokens in order; if they do not concatenate back
        # to the transcript, the user is shown text that was never said.
        lines, _ = romanize.romanize_transcript(text, lang)
        assert "".join(tok["t"] for tok in lines[0]) == text

    @pytest.mark.parametrize("text,lang", SCRIPT_SAMPLES)
    def test_every_reading_is_latin_script(self, text, lang):
        # A reading exists to be readable by someone who cannot read the
        # source script, so no character of that script may leak into it.
        # Diacritics are fine - pinyin needs them - so compare on the base
        # letters with combining marks stripped.
        lines, _ = romanize.romanize_transcript(text, lang)
        for tok in lines[0]:
            if not tok.get("r"):
                continue
            base = "".join(
                c for c in unicodedata.normalize("NFD", tok["r"])
                if not unicodedata.combining(c)
            )
            assert base.isascii(), f"reading {tok['r']!r} is not Latin script"

    def test_pinyin_tone_marks_are_the_documented_exception(self):
        # Pinyin is the one system that legitimately uses non-ascii diacritics.
        lines, _ = romanize.romanize_transcript("你好", "zh")
        assert not all(tok["r"].isascii() for tok in lines[0])

    def test_line_structure_is_preserved_including_blank_lines(self):
        lines, _ = romanize.romanize_transcript("你好\n\n世界", "zh")
        assert len(lines) == 3
        assert lines[1] == []  # the paragraph break

    def test_no_token_is_ever_empty(self):
        lines, _ = romanize.romanize_transcript("你好 world 世界", "zh")
        assert all(tok["t"] for tok in lines[0])


# --------------------------------------------------------------------------
# Flattening for copy and .txt download
# --------------------------------------------------------------------------

class TestInterleavedText:
    def test_reading_is_written_under_the_original_line(self):
        lines, _ = romanize.romanize_transcript("你好", "zh")
        assert romanize.to_interleaved_text(lines) == "你好\nnǐ hǎo"

    def test_blank_lines_survive_the_flattening(self):
        lines, _ = romanize.romanize_transcript("你好\n\n世界", "zh")
        assert romanize.to_interleaved_text(lines) == "你好\nnǐ hǎo\n\n世界\nshì jiè"

    def test_a_line_with_no_readings_is_emitted_once(self):
        assert romanize.to_interleaved_text([[{"t": "Hello world"}]]) == "Hello world"

    @pytest.mark.parametrize("text,lang", SCRIPT_SAMPLES)
    def test_original_text_always_appears_verbatim(self, text, lang):
        lines, _ = romanize.romanize_transcript(text, lang)
        assert text in romanize.to_interleaved_text(lines)


class TestSystemName:
    @pytest.mark.parametrize("lang,expected", [
        ("zh", "Pinyin"),
        ("ja", "Romaji"),
        ("ko", "Revised Romanization"),
        ("ru", "Transliteration"),
        ("hi", "Transliteration"),
    ])
    def test_named_per_language(self, lang, expected):
        assert romanize.system_name(lang) == expected

    def test_falls_back_to_sniffing_the_script(self):
        assert romanize.system_name("xx", "你好") == "Pinyin"
        assert romanize.system_name("xx", "ひらがな") == "Romaji"
        assert romanize.system_name("xx", "한국어") == "Revised Romanization"

from dictation.text import clean_transcript


def test_strips_and_capitalizes_with_trailing_space():
    assert clean_transcript("  hello world  ") == "Hello world "


def test_no_trailing_space_no_capitalize():
    out = clean_transcript(
        "hello", capitalize_first=False, trailing_space=False
    )
    assert out == "hello"


def test_collapses_internal_whitespace_and_newlines():
    assert clean_transcript("hello\n  there\tfriend") == "Hello there friend "


def test_empty_input_returns_empty():
    assert clean_transcript("") == ""
    assert clean_transcript("   ") == ""


def test_silence_hallucinations_dropped():
    for phrase in ["Thank you.", "thanks for watching!", "you", "..."]:
        assert clean_transcript(phrase) == ""


def test_real_sentence_with_hallucination_word_kept():
    # "you" alone is dropped, but inside a sentence it is preserved.
    assert clean_transcript("you are amazing") == "You are amazing "


def test_already_capitalized_unchanged():
    assert clean_transcript("Hello there", trailing_space=False) == "Hello there"

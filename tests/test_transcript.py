from agx.utils.transcript import clean_title_text


def test_clean_title_text():
    # Strip user request tags and prefixes
    cleaned = clean_title_text("please fix the broken login component")
    assert cleaned == "The broken login component"

    # Strip code blocks and leading 'explain' prefix
    raw_code = "Explain this function: ```python\ndef foo(): pass\n``` please"
    cleaned = clean_title_text(raw_code)
    assert cleaned == "This function: please"

    # Strip conversational filler prefixes
    assert clean_title_text("so can you create a dockerfile") == "A dockerfile"
    assert clean_title_text("ok help me build a website") == "A website"
    assert clean_title_text("analyze memory leak") == "Analyze memory leak"

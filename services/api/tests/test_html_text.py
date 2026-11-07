from app.ingestion.html_text import html_to_paragraphs


def test_paragraphs_links_and_lists():
    html = (
        "<p>First para with <a href='https://x.test'>link text</a>.</p>"
        "<p>Symptoms include</p><ul><li>One</li><li> Two  words </li></ul><p>Last</p>"
    )
    assert html_to_paragraphs(html) == [
        "First para with link text.",
        "Symptoms include",
        "- One\n- Two words",
        "Last",
    ]


def test_entities_whitespace_and_scripts():
    html = "<p>Fish &amp; chips\n  are   here</p><script>alert(1)</script><style>p{}</style>"
    assert html_to_paragraphs(html) == ["Fish & chips are here"]


def test_empty_and_plain_text_input():
    assert html_to_paragraphs("") == []
    assert html_to_paragraphs("   ") == []
    assert html_to_paragraphs("Just text") == ["Just text"]


def test_unclosed_list_is_kept():
    assert html_to_paragraphs("<ul><li>A<li>B") == ["- A\n- B"]


def test_output_contains_no_markup():
    result = html_to_paragraphs("<p onclick='x()'>Hi <b>there</b></p><img src='x'>")
    assert result == ["Hi there"]

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


def test_table_rows_keep_each_value_next_to_its_label():
    html = (
        "<p>Intro line:</p><table><tr><th>Category</th><th>Low</th><th>High</th></tr>"
        "<tr><td>Alpha</td><td>10</td><td>20</td></tr><tr><td>Beta</td><td>30</td><td>40</td></tr>"
        "</table><p>After the table.</p>"
    )
    assert html_to_paragraphs(html) == [
        "Intro line:",
        "Category | Low | High\nAlpha | 10 | 20\nBeta | 30 | 40",
        "After the table.",
    ]


def test_empty_cells_and_nested_blocks_in_cells():
    html = "<table><tr><td>A</td><td></td><td><p>C</p><p>D</p></td></tr></table>"
    assert html_to_paragraphs(html) == ["A |  | C D"]


def test_table_caption_is_kept_as_its_own_line():
    html = "<table><caption>Synthetic caption</caption><tr><td>X</td><td>1</td></tr></table>"
    assert html_to_paragraphs(html) == ["Synthetic caption\nX | 1"]


def test_unclosed_table_is_flushed():
    assert html_to_paragraphs("<table><tr><td>A<td>B") == ["A | B"]


def test_lists_after_tables_still_work():
    html = "<table><tr><td>A</td></tr></table><ul><li>One</li></ul>"
    assert html_to_paragraphs(html) == ["A", "- One"]

import pytest

from app.ingestion.chunking import approx_tokens, chunk_paragraphs


def words(n, prefix="w"):
    return " ".join(f"{prefix}{i}" for i in range(n))


def test_short_input_is_one_chunk():
    chunks = chunk_paragraphs(["Short one.", "Short two."], max_tokens=100, overlap_tokens=10)
    assert chunks == ["Short one.\n\nShort two."]


def test_every_chunk_respects_the_limit():
    paragraphs = [f"Sentence {i} is here. Another sentence {i} follows." for i in range(60)]
    chunks = chunk_paragraphs(paragraphs, max_tokens=60, overlap_tokens=10)
    assert len(chunks) > 3
    assert all(approx_tokens(chunk) <= 60 for chunk in chunks)


def test_overlap_repeats_the_tail_of_the_previous_chunk():
    paragraphs = [f"Paragraph number {i} has a few words in it." for i in range(30)]
    chunks = chunk_paragraphs(paragraphs, max_tokens=40, overlap_tokens=20)
    assert len(chunks) > 2
    first_tail = chunks[0].split("\n\n")[-1]
    assert first_tail in chunks[1]


def test_no_overlap_means_no_repeated_paragraphs():
    paragraphs = [f"Paragraph number {i} has a few words in it." for i in range(30)]
    chunks = chunk_paragraphs(paragraphs, max_tokens=40, overlap_tokens=0)
    joined = "\n\n".join(chunks).split("\n\n")
    assert joined == paragraphs


def test_all_text_is_preserved_in_order():
    paragraphs = [f"Unique marker {i} appears once." for i in range(40)]
    chunks = chunk_paragraphs(paragraphs, max_tokens=50, overlap_tokens=10)
    text = "\n\n".join(chunks)
    positions = [text.index(f"marker {i} ") for i in range(40)]
    assert positions == sorted(positions)


def test_oversize_sentence_is_split_on_words():
    chunks = chunk_paragraphs([words(400)], max_tokens=50, overlap_tokens=0)
    assert len(chunks) > 5
    assert all(approx_tokens(chunk) <= 50 for chunk in chunks)
    assert " ".join(chunks).split() == words(400).split()


def test_empty_input_and_blank_paragraphs():
    assert chunk_paragraphs([]) == []
    assert chunk_paragraphs(["", "   "]) == []


@pytest.mark.parametrize("max_tokens,overlap", [(0, 0), (10, 10), (10, 11), (10, -1)])
def test_invalid_parameters_are_rejected(max_tokens, overlap):
    with pytest.raises(ValueError):
        chunk_paragraphs(["x"], max_tokens=max_tokens, overlap_tokens=overlap)

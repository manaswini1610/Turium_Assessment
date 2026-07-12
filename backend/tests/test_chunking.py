from app.services.chunking_service import chunk_text


def test_chunk_text_short_text_returns_single_chunk():
    text = "This is a short note about the leave policy."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text.strip()


def test_chunk_text_empty_or_blank_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("    \n\t") == []


def test_chunk_text_long_text_produces_multiple_overlapping_chunks():
    long_text = "sample word " * 2000  # far more than 500 tokens
    chunks = chunk_text(long_text, chunk_size=500, overlap=100)

    assert len(chunks) > 1
    for chunk in chunks:
        assert isinstance(chunk, str)
        assert len(chunk) > 0


def test_chunk_text_custom_size_respected():
    long_text = "word " * 1000
    chunks_small = chunk_text(long_text, chunk_size=100, overlap=20)
    chunks_large = chunk_text(long_text, chunk_size=500, overlap=100)

    assert len(chunks_small) > len(chunks_large)

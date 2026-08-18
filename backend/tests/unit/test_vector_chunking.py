from backend.app.utils.chunker import TextChunker


def test_chunk_email_message_sliding_window():
    short_text = "This is a short email."
    chunks = TextChunker.chunk_email_message(short_text)
    assert len(chunks) == 1
    assert chunks[0] == "This is a short email."

    long_text = "A" * 2500
    long_chunks = TextChunker.chunk_email_message(long_text, max_chars=1000, overlap=100)
    assert len(long_chunks) >= 3


def test_chunk_document_extraction_page_boundaries():
    doc_text = (
        "--- [Page 1] ---\n"
        "Invoice #9921 Total Due: $4,500.00 Vendor: Acme Enterprise Solutions\n\n"
        "--- [Page 2] ---\n"
        "Payment Terms: Net 30. Wire transfer details..."
    )

    chunks = TextChunker.chunk_document_extraction(doc_text)
    assert len(chunks) == 2
    assert chunks[0][1] == 1  # Page number 1
    assert "Invoice #9921" in chunks[0][0]
    assert chunks[1][1] == 2  # Page number 2
    assert "Payment Terms" in chunks[1][0]

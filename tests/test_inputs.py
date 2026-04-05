from pathlib import Path

from url_s_to_markdown.inputs import chunk_urls, parse_url_stats, parse_urls, parse_urls_from_text_block


def test_parse_urls_deduplicate_and_ignore_empty(tmp_path: Path):
    input_file = tmp_path / "urls.txt"
    input_file.write_text(
        "\nhttps://example.com\nhttps://example.com\n\nhttps://openai.com\n",
        encoding="utf-8",
    )

    urls = parse_urls(
        single_url="https://example.com",
        urls=["https://openai.com", "", "invalid-url"],
        file_path=str(input_file),
    )

    assert urls == ["https://example.com", "https://openai.com"]


def test_url_counter_stats(tmp_path: Path):
    input_file = tmp_path / "urls.txt"
    input_file.write_text("https://a.com\ninvalid\n\nhttps://a.com\n", encoding="utf-8")
    stats = parse_url_stats(file_path=str(input_file))

    assert stats.total_detected == 3
    assert len(stats.valid_urls) == 2
    assert len(stats.unique_urls) == 1
    assert len(stats.invalid_urls) == 1


def test_chunk_urls_auto_batching():
    batches = chunk_urls(["u1", "u2", "u3", "u4", "u5"], max_urls=2)
    assert batches == [["u1", "u2"], ["u3", "u4"], ["u5"]]


def test_parse_urls_from_text_block():
    text_block = "\nhttps://a.com\n  https://b.com/path \n\n"
    assert parse_urls_from_text_block(text_block) == ["https://a.com", "https://b.com/path"]

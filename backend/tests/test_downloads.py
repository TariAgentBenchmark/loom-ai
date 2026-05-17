from app.utils.downloads import normalize_filename_for_content


def test_normalize_filename_for_content_replaces_wrong_image_extension():
    filename = normalize_filename_for_content(
        "result.png",
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00",
    )

    assert filename == "result.jpg"


def test_normalize_filename_for_content_keeps_matching_image_extension():
    filename = normalize_filename_for_content(
        "result.png",
        b"\x89PNG\r\n\x1a\n",
    )

    assert filename == "result.png"


def test_normalize_filename_for_content_adds_missing_extension():
    filename = normalize_filename_for_content(
        "result",
        b"RIFF\x00\x00\x00\x00WEBP",
    )

    assert filename == "result.webp"

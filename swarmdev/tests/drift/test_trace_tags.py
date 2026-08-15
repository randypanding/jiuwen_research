from swarmdev.drift import TAG_PATTERN, scan_dir, scan_text


def test_tag_pattern_positive():
    assert TAG_PATTERN.search("@REQ-CL-X1@") is not None
    assert TAG_PATTERN.findall("a @REQ-CL-X1@ b @REQ-CL-A2_B-3@ c") == [
        "CL-X1", "CL-A2_B-3",
    ]


def test_tag_pattern_negative():
    assert TAG_PATTERN.search("@REQ-@") is None
    assert TAG_PATTERN.search("REQ-CL-X1") is None
    assert TAG_PATTERN.search("@req-CL-X1@") is None
    assert TAG_PATTERN.search("@REQ-cl-x1@") is None
    assert TAG_PATTERN.search("@REQ-CL X1@") is None


def test_scan_text_collects_unique_tags():
    src = "x = 1  # @REQ-CL-A1@\ny = 2  # @REQ-CL-A1@ and @REQ-CL-A2@"
    assert scan_text(src) == {"CL-A1", "CL-A2"}
    assert scan_text("") == set()
    assert scan_text("no tags here @REQ-@") == set()


def test_scan_dir_multi_file(tmp_path):
    (tmp_path / "a.py").write_text("# @REQ-CL-A1@ @REQ-CL-A2@\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.py").write_text("# @REQ-CL-B1@\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("@REQ-CL-TXT@\n", encoding="utf-8")
    (tmp_path / "empty.py").write_text("no tags\n", encoding="utf-8")
    found = scan_dir(tmp_path)
    assert found == {"a.py": {"CL-A1", "CL-A2"}, "sub/b.py": {"CL-B1"}}


def test_scan_dir_custom_suffixes(tmp_path):
    (tmp_path / "a.py").write_text("@REQ-CL-A1@", encoding="utf-8")
    (tmp_path / "b.md").write_text("@REQ-CL-B1@", encoding="utf-8")
    assert scan_dir(tmp_path, suffixes=(".md",)) == {"b.md": {"CL-B1"}}


def test_scan_dir_missing_root(tmp_path):
    assert scan_dir(tmp_path / "nope") == {}

"""Tests of the dataset gallery (results shown instantly from the cache of the real pipeline output). Run: python -I demo/tests/test_gallery.py"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import gallery as G  # noqa: E402


def test_cache_has_all_cases_and_the_scoreboard_adds_up():
    assert G.available()
    d = G.data()
    assert d["summary"]["cases"] == 120 == len(d["cases"])
    assert d["summary"]["green"] + d["summary"]["amber"] + d["summary"]["red"] == 120
    shown = d["summary"]["green"] + d["summary"]["amber"]
    for k, v in d["scoreboard"].items():
        assert v["hits"] + v["misses"] == v["true_cases"], k
        assert v["hits"] + v["misses"] + v["false_alarms"] + v["correct_negatives"] == shown, k


def test_red_photos_show_no_findings_and_every_case_has_a_picture():
    d = G.data()
    for c in d["cases"]:
        if c["light"] == "RED":
            assert all(v is None for v in c["detected"].values()), c["name"]
        assert os.path.exists(os.path.join(G.PHOTOS, c["name"] + ".jpg")), c["name"]


def test_verdict_words_and_dark_mode_class():
    assert G.verdict(True, True)[0].startswith("HIT") and G.verdict(True, False)[0].startswith("MISSED")
    assert G.verdict(False, True)[0].startswith("FALSE ALARM") and G.verdict(False, False)[0].startswith("correct")
    assert G.verdict(True, None)[0].startswith("not shown")
    d = G.data()
    name = d["cases"][0]["name"]
    img, h1, h2 = G.show(name)
    assert os.path.exists(img) and "hh-light" in h1 and "hh-light" in G.scoreboard_html() and "hh-light" in h2
    text = re.sub("<[^>]+>", " ", G.scoreboard_html())
    assert "not real phone photos" in text and "false alarms" in text.lower()


def test_dropdown_lists_every_case_with_its_truth():
    ch = G.choices()
    assert len(ch) == 120 and all("true:" in label for label, _ in ch)
    assert G.default_case() in [v for _, v in ch]


def test_truth_box_for_a_dataset_picture_and_nothing_for_others():
    d = G.data()
    c = next(x for x in d["cases"] if any(x["truth"].values()) and x["light"] == "GREEN")
    a = {"findings": [], "extra": [dict(cls="AF", src="B", detected=True)]}
    box = G.truth_box(c["name"] + ".jpg", a)
    assert "hh-light" in box and "true answer" in box.lower() and "simulated" not in box.lower() and "dataset" not in box.lower().replace("true answer next to what the tool said", "")
    assert G.truth_box("sample1_straight_clean.jpg", a) == "" and G.truth_box(None, a) == ""


def test_example_folder_holds_dataset_pictures_with_a_key():
    ex = os.path.join(HERE, "..", "dataset_examples")
    files = [f for f in os.listdir(ex) if f.lower().endswith(".jpg")]
    assert len(files) >= 10 and all(f.startswith("N") for f in files) and os.path.exists(os.path.join(ex, "KEY.csv"))


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print("ok  ", name)
    print(n, "tests passed")

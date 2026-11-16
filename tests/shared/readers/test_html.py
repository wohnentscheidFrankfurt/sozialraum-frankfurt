from types import SimpleNamespace

from pipeline.shared.readers.html import example_texts, html_text


def test_html_text_drops_scripts_tags_and_entities(tmp_path):
    p = tmp_path / "page.html"
    p.write_text("<html><head><script>var x = 'Fonds';</script><style>p {}</style></head>"
                 "<body><p>Industria&nbsp;Wohnen <b>kauft</b> &amp; baut</p></body></html>", encoding="utf-8")
    assert html_text(p).split() == ["Industria", "Wohnen", "kauft", "&", "baut"]


def test_html_text_drops_comments(tmp_path):
    p = tmp_path / "page.html"
    p.write_text("<p>Fonds</p><!-- <p>Hamburg Trust\n besitzt</p> --><p>kauft</p>", encoding="utf-8")
    assert html_text(p).split() == ["Fonds", "kauft"]


def test_example_texts_reads_web_pages_by_their_suffix(tmp_path):
    page = tmp_path / "a.html"
    page.write_text("<p>B&nbsp;besitzt</p><!-- <p>C</p> -->", encoding="utf-8")
    texts = example_texts(SimpleNamespace(B_HTML=page), [{"name": "B", "source": "B_HTML", "phrases": []}])
    assert texts == {"B_HTML": " B besitzt  "}

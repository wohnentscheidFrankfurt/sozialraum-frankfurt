from pipeline.map.html.sources import read_web


def test_read_web_reads_every_part(tmp_path):
    (tmp_path / "js").mkdir()
    (tmp_path / "leaflet").mkdir()
    (tmp_path / "fonts").mkdir()
    (tmp_path / "map.html").write_text("<html></html>")
    (tmp_path / "map.css").write_text("body{}")
    (tmp_path / "leaflet" / "leaflet.css").write_text(".leaflet{}")
    (tmp_path / "leaflet" / "leaflet.js").write_text("var L={};")
    (tmp_path / "js" / "02_b.js").write_text("zwei();")
    (tmp_path / "js" / "01_a.js").write_text("eins();")
    template, parts = read_web(tmp_path)
    assert template == "<html></html>"
    assert set(parts) == {"/*__LEAFLET_CSS__*/", "/*__FONTS__*/", "/*__MAP_CSS__*/", "/*__LEAFLET_JS__*/", "/*__MAP_JS__*/"}
    assert parts["/*__MAP_JS__*/"] == "eins();\nzwei();" and parts["/*__FONTS__*/"] == ""

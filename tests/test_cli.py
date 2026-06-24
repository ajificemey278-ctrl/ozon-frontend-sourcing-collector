import json

from ozon_frontend_sourcing_collector.cli import main


def test_cli_build_url_outputs_json(capsys):
    code = main(["build-url", "--platform", "1688", "--keyword", "LED仿真蜡烛 遥控 3件套"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["platform"] == "1688"
    assert "s.1688.com" in payload["url"]
    assert "%D2%A3%BF%D8" in payload["url"]

def test_cli_parse_text_accepts_stdin(monkeypatch, capsys):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("LED露营灯\n¥12.50\n月销 100+\n"))
    code = main(["parse-text", "--platform", "taobao", "--url", "https://item.taobao.com/item.htm?id=1", "--input", "-"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["items"][0]["price_value"] == 12.5
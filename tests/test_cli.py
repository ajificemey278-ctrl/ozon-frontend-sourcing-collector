import json

from ozon_frontend_sourcing_collector.cli import main


def test_cli_build_url_outputs_json(capsys):
    code = main(["build-url", "--platform", "1688", "--keyword", "LED仿真蜡烛 遥控 3件套"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["platform"] == "1688"
    assert "s.1688.com" in payload["url"]
    assert "%D2%A3%BF%D8" in payload["url"]
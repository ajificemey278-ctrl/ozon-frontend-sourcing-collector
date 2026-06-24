from ozon_frontend_sourcing_collector.encoding import build_search_url, encode_1688_keyword


def test_1688_keyword_uses_gb18030_percent_encoding():
    encoded = encode_1688_keyword("LED仿真蜡烛 遥控 3件套")
    assert "%B7%C2%D5%E6" in encoded
    assert "%D2%A3%BF%D8" in encoded
    assert "%CC%D7" in encoded


def test_build_urls_for_all_platforms():
    assert "ozon.ru/search" in build_search_url("ozon", "фонарь")
    assert "s.1688.com" in build_search_url("1688", "露营灯")
    assert "s.taobao.com" in build_search_url("taobao", "露营灯")
    assert "yiwugo.com" in build_search_url("yiwugo", "露营灯")
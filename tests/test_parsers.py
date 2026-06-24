from ozon_frontend_sourcing_collector.parsers import parse_html_snapshot, parse_visible_text


def test_parse_ozon_visible_text_price_delivery_reviews():
    text = """Светодиодные свечи на батарейках с пультом, 3 шт
38,47 ¥
5.0 127 отзывов
Доставим 11 июля
"""
    result = parse_visible_text("ozon", "https://www.ozon.ru/product/test-123/", text)
    assert result.status == "ok"
    item = result.items[0]
    assert item.currency == "CNY"
    assert item.price_value == 38.47
    assert item.delivery_text
    assert item.product_id == "123"


def test_parse_1688_html_detail_fields():
    html = """
    <html><head><title>led电子蜡烛灯 遥控仿真光</title></head>
    <body>
      <h1>led电子蜡烛灯 遥控仿真光面摇摆蜡烛婚庆派对氛围灯装饰品发光</h1>
      <div>¥17.00 已售 6800+ 1个起批 义乌市水意方工艺品有限公司 包邮</div>
      <img src="//cbu01.alicdn.com/img/test.jpg" />
    </body></html>
    """
    result = parse_html_snapshot("1688", "https://detail.1688.com/offer/831761233230.html", html)
    assert result.status == "ok"
    item = result.items[0]
    assert item.currency == "CNY"
    assert item.price_value == 17.0
    assert item.sales_text
    assert item.product_id == "831761233230"
    assert item.attributes["remote"] == "遥控"


def test_parse_search_page_adds_card_candidates():
    html = """
    <html><head><title>搜索结果</title></head><body>
      <p>这是一段很长的搜索页文本，用来模拟前端结果页。</p>
      <div>{}</div>
      <a href="https://detail.1688.com/offer/675208194190.html">电子蜡烛生日浪漫表白 led 遥控 3件套 ¥22 已售6.4万+件</a>
    </body></html>
    """.format("搜索内容" * 400)
    result = parse_html_snapshot("1688", "https://s.1688.com/selloffer/offer_search.htm", html)
    assert result.status == "ok"
    assert len(result.items) >= 2
    assert result.items[1].product_id == "675208194190"
    assert result.items[1].price_value == 22.0

def test_parse_taobao_visible_text_supplier_fields():
    text = """太阳能露营灯 USB充电 户外帐篷灯
¥39.90
月销 1000+
包邮
杭州户外用品店
"""
    result = parse_visible_text("taobao", "https://item.taobao.com/item.htm?id=123456", text)
    assert result.status == "ok"
    item = result.items[0]
    assert item.currency == "CNY"
    assert item.price_value == 39.90
    assert item.sales_text.startswith("月销")
    assert item.product_id == "123456"
    assert item.attributes["usb"] == "USB"


def test_parse_yiwugo_visible_text_supplier_fields():
    text = """义乌购 LED露营灯 太阳能充电户外帐篷灯
¥12.50
起订量 2件
店铺：义乌市某某电子商行
48小时发货
"""
    result = parse_visible_text("yiwugo", "https://www.yiwugo.com/product/detail/987654.html", text)
    assert result.status == "ok"
    item = result.items[0]
    assert item.currency == "CNY"
    assert item.price_value == 12.5
    assert item.product_id == "987654"
    assert item.attributes["quantity"] == "2件"
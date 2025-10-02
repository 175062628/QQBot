import datetime
from zoneinfo import ZoneInfo

import requests
import json
from .uu_data_model import *
import time

def crawl_goods(goods_list, interval):
    url = "https://api.youpin898.com/api/homepage/es/commodity/GetCsGoPagedList"
    res = []

    for goods in goods_list:
        payload = json.dumps({
            "hasSold": "true",
            "haveBuZhangType": 0,
            "listSortType": "1",
            "listType": 10,
            "pageIndex": 1,
            "pageSize": 1,
            "sortType": "1",
            "status": "20",
            "stickersIsSort": False,
            "templateId": f"{goods}",
            "userId": ""
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload).json()

        market_model = prase_json(response)

        if market_model is not None:
            res.append(market_model)

        time.sleep(interval)

    return res


def prase_json(response):
    if response["Code"] != 0 or response["Data"] is None or len(response["Data"]) == 0 or response["Data"]["TemplateInfo"] is None:
        return None

    name = response["Data"]["TemplateInfo"]["CommodityName"] \
        if response["Data"]["TemplateInfo"]["CommodityName"] is not None else ''

    template_id = response["Data"]["TemplateInfo"]["Id"] \
        if response["Data"]["TemplateInfo"]["Id"] is not None else ''

    min_price = float(response["Data"]["TemplateInfo"]["MinPrice"]) \
        if response["Data"]["TemplateInfo"]["MinPrice"] is not None else 0

    on_sale_count = response["Data"]["TemplateInfo"]["OnSaleCount"] \
        if response["Data"]["TemplateInfo"]["OnSaleCount"] is not None else 0

    on_lease_count = response["Data"]["TemplateInfo"]["OnLeaseCount"] \
        if response["Data"]["TemplateInfo"]["OnLeaseCount"] is not None else 0

    lease_unit_price = float(response["Data"]["TemplateInfo"]["LeaseUnitPrice"]) \
        if response["Data"]["TemplateInfo"]["LeaseUnitPrice"] is not None else 0

    long_lease_unit_price = float(response["Data"]["TemplateInfo"]["LongLeaseUnitPrice"]) \
        if response["Data"]["TemplateInfo"]["LongLeaseUnitPrice"] is not None else 0

    lease_deposit = float(response["Data"]["TemplateInfo"]["LeaseDeposit"]) \
        if response["Data"]["TemplateInfo"]["LeaseDeposit"] is not None else 0

    return MarketModel(
        datetime.datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S"),
        name,
        str(template_id),
        min_price,
        on_sale_count,
        on_lease_count,
        lease_unit_price,
        long_lease_unit_price,
        lease_deposit
    )
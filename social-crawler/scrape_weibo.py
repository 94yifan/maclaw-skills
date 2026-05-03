#!/usr/bin/env python3
"""Scape Weibo brand content using CDP (port 9333)"""
import json
import sys
from websocket import create_connection

BRANDS = [
    ("瑞幸咖啡", "luckincoffee瑞幸咖啡", "6349791448"),
    ("库迪", "CottiCoffee库迪咖啡", "7791266545"),
    ("古茗", "古茗茶饮", "2809775704"),
    ("茉莉奶白", "茉莉奶白MollyTea", "7577524421"),
    ("霸王茶姬", "霸王茶姬CHAGEE", "5652018762"),
    ("喜茶", "喜茶", "2804387887"),
    ("星巴克", "星巴克中国", None),
    ("茶百道", "茶百道ChaPanda", "6502206666"),
    ("奈雪的茶", "奈雪的茶", "5884674413"),
    ("CoCo", "CoCo都可官方", "2030619861"),
    ("爷爷不泡茶", "爷爷不泡茶官方微博", "7769072120"),
    ("沪上阿姨", "沪上阿姨", "3921865344"),
    ("乐乐茶", "楽楽茶LELECHA", "6253473981"),
    ("皮爷咖啡", "PeetsCoffee皮爷咖啡", "6360528436"),
    ("M Stand", "MStand", "6345199298"),
    ("Manner", "MANNER官微", "6808111794"),
    ("茉酸奶", "茉酸奶MOREYOGURT", "5188894132"),
    ("树夏酸奶", "树夏", "7144806571"),
]

def cdp_send(ws, method, params=None):
    id = 1
    msg = {"id": id, "method": method}
    if params:
        msg["params"] = params
    ws.send(json.dumps(msg))
    resp = ws.recv()
    return json.loads(resp)

def get_weibo_tabs():
    """Get all open Chrome tabs from CDP"""
    ws = create_connection("ws://127.0.0.1:9333/devtools/page/F78E893FCA7C234D3D5CF21E7D260D43")
    resp = cdp_send(ws, "Target.getTargets")
    ws.close()
    return resp

if __name__ == "__main__":
    print(json.dumps(get_weibo_tabs(), indent=2))

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec_api as R
tok = R.token()
page = ""
tot = conf = conf_pcs = 0
pend = []
while True:
    d = R.call("GET", f"{R.BASE}?page_size=500&page_token={page}", tok)
    data = d.get("data", {})
    for r in data.get("items", []):
        f = r.get("fields", {})
        tot += 1
        note = R.g(f, "份数备注")
        pcs = 1
        if isinstance(note, str):
            ds = "".join(ch for ch in note if ch.isdigit())
            if ds:
                pcs = int(ds)
        c = f.get("地址复核")
        if c is True:
            conf += 1
            conf_pcs += pcs
    if not data.get("has_more"):
        break
    page = data.get("page_token", "")
print(f"总记录 {tot} | 地址复核已勾 {conf} 条 | 勾选折算份数 {conf_pcs}")

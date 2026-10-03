import json,sys,urllib.request,urllib.parse,os
sys.path.insert(0,'tmp/giftlist')
import rec_api as R
tok=R.token()
p=""
rows=[]
while True:
    d=R.call("GET", f"{R.BASE}?page_size=500&page_token={urllib.parse.quote(p)}", tok)
    data=d.get("data",{})
    for r in data.get("items",[]):
        f=r.get("fields",{})
        rows.append((R.g(f,'序号'),R.g(f,'名字'),R.g(f,'公司'),R.g(f,'收件信息'),f.get('地址复核'),f.get('分类'),r['record_id']))
    if not data.get("has_more"): break
    p=data.get("page_token","")
def key(x):
    try: return int(x[0])
    except: return 99999
rows.sort(key=key)
print("总行数",len(rows))
for r in rows:
    if isinstance(r[0],int) or str(r[0]).isdigit():
        print(f"{r[0]} | {r[1]} | {r[2]} | {str(r[3])[:60]} | 复核={r[4]} | {r[5]}")

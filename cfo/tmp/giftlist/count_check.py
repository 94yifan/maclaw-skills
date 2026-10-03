import sys
sys.path.insert(0,'tmp/giftlist')
import rec_api as R, urllib.parse
tok=R.token()
p=""; tot=0; yes=0; no=0; empty=0
unchecked=[]
while True:
    d=R.call("GET", f"{R.BASE}?page_size=500&page_token={urllib.parse.quote(p)}", tok)
    data=d.get("data",{})
    for r in data.get("items",[]):
        f=r.get("fields",{})
        tot+=1
        v=f.get('地址复核')
        if v is True: yes+=1
        elif v is False: no+=1
        else:
            empty+=1
            unchecked.append((R.g(f,'序号'),R.g(f,'名字'),R.g(f,'公司')))
    if not data.get("has_more"): break
    p=data.get("page_token","")
print(f"总记录 {tot} | 已确认(核勾) {yes} | 明确否 {no} | 未处理 {empty}")
def k(x):
    try: return int(x[0])
    except: return 99999
unchecked.sort(key=k)
print("未处理明细：")
for u in unchecked:
    print(f"  {u[0]} | {u[1]} | {u[2]}")

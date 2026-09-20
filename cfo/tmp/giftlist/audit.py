#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中秋礼单只读审计脚本（全局问题必带审计 + 记录级/字段级变更对账）。

用法（从任意 cwd 均可运行，路径全部基于 __file__ 推导）:
  python3 <abs>/cfo/tmp/giftlist/audit.py [--no-snapshot]

输出: 总记录 / 已勾 / 明确否 / 未处理 / 同电话重复组 / 同地址重复组 / 序号缺口
     + 变更对账（vs 最近一份「别的日期」的主快照）: 新增 / 消失 / 缺口增量 / 表内他改（字段级）
只读表数据；在 <脚本目录>/snapshots/ 下落快照：
  - snap_YYYY-MM-DD.json       当日主快照（每次运行覆盖，供次日对账）
  - snap_YYYY-MM-DD_HHMM.json  不可变时间快照（保留当日多次读数）

守卫（写入脚本即生效，不依赖人记）:
  - 序号一律读回，不推算（快照以表内真实序号为键）
  - 记录级对账：新增/消失（守卫D）
  - 字段级对账：序号相同但字段变化 → 「表内他改」（守卫K）
  - 缺口增量对账：建后即删的记录只留缺口、内容对账看不见 → 单列「新增缺口/补齐缺口」
  - 统计口径：每条记录算一份，子记录也有礼品，不按父记录折叠
"""
import sys, re, collections, os, json, glob, datetime, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rec_api as R

SNAP_DIR = os.path.join(HERE, 'snapshots')
# 只用「当日主快照」做跨日对账；_HHMM 时间快照与 full_*.json 不参与
SNAP_RE = re.compile(r'^snap_\d{4}-\d{2}-\d{2}\.json$')

# 参与字段级对账的字段
FLDS = ('名字', '公司', '收件信息', '电话', '分类', '地址复核', '份数备注')

# 预期重复白名单（2026-09-14 逸凡确认；命中即不作为缺陷，仅单独列出）
#   同电话 13795389815 → 序号 301/308：8号桥两份，一份写名字、一份不写
#   同地址 → 序号 303/304：清闲两位不同的人，各寄一份
#             序号 301/308：8号桥同址两份（同上）
#   同电话 17818004335 / 同地址 → 序号 105/316/317：榴芒一刻 Harlie 与其子记录（父记录关联，
#             2026-09-15 表内已建父子关系，属一份地址多收件人，非重复录入）
#   父记录簇：50→243/244/245，86→266，105→316/317，110→263，230→325，241→250-253，
#             257→259→260→261，264→265
#   重要（2026-09-15 逸凡确认）：子记录也有礼品，“一父带三子 = 四份”。统计份数时
#     **每条记录算一份，不按父记录折叠**；全表记录数即礼品份数。别再折叠子记录。
# 维护方式：逸凡确认某组重复为“故意要两份”时，把电话/序号对加进来。
EXPECTED_PHONE = {"13795389815", "17818004335"}
EXPECTED_ADDR_PAIRS = {frozenset(("303", "304")), frozenset(("301", "308")),
                       frozenset(("105", "316")), frozenset(("105", "317"))}


def g(f, k):
    v = f.get(k)
    if isinstance(v, list):
        return "".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in v)
    if isinstance(v, dict):
        return v.get("text", "")
    return v


def snap_fields(f):
    """把一条记录压成对账用的扁平字典（全字段，守卫K）。"""
    info = str(g(f, '收件信息') or '')
    return {
        '名字': str(g(f, '名字') or ''),
        '公司': str(g(f, '公司') or ''),
        '收件信息': info,
        '电话': (re.findall(r'1[3-9]\d{9}', info) or [''])[0],
        '分类': str(g(f, '分类') or ''),
        '地址复核': f.get('地址复核') is True,
        '份数备注': str(g(f, '份数备注') or ''),
    }


def do_snapshot(rows, g):
    """记录级（守卫D）+ 字段级（守卫K）变更对账。"""
    os.makedirs(SNAP_DIR, exist_ok=True)
    now = datetime.datetime.now()
    today = now.date().isoformat()
    cur = {}
    for f in rows:
        n = str(g(f, '序号') or '').strip()
        if not n:
            continue
        cur[n] = snap_fields(f)

    main_path = os.path.join(SNAP_DIR, f'snap_{today}.json')
    with open(main_path, 'w') as fh:
        json.dump(cur, fh, ensure_ascii=False, indent=1)
    # 当日多次读数保留：不可变时间快照（解决「一天内多次读数只留最后一次」）
    imm_path = os.path.join(SNAP_DIR, f'snap_{today}_{now.strftime("%H%M")}.json')
    with open(imm_path, 'w') as fh:
        json.dump(cur, fh, ensure_ascii=False, indent=1)

    prev_files = [p for p in sorted(glob.glob(os.path.join(SNAP_DIR, 'snap_*.json')))
                  if SNAP_RE.match(os.path.basename(p))
                  and os.path.basename(p) != os.path.basename(main_path)]
    if not prev_files:
        print(f"\n变更对账: 无历史快照（本次为基线 {os.path.basename(main_path)}）")
        return
    with open(prev_files[-1]) as fh:
        prev = json.load(fh)
    tag = os.path.basename(prev_files[-1])

    added = [k for k in cur if k not in prev]
    gone = [k for k in prev if k not in cur]
    print(f"\n变更对账 vs {tag}: 新增 {len(added)} 条 / 消失 {len(gone)} 条")
    for k in sorted(added, key=lambda x: int(x) if x.isdigit() else 0):
        v = cur[k]
        print(f"  + 序号{k} {v['名字']} | {v['公司']} | {v['电话']}")
    for k in sorted(gone, key=lambda x: int(x) if x.isdigit() else 0):
        v = prev[k]
        print(f"  - 序号{k} {v['名字']} | {v['公司']} | {v.get('电话','')}")
    if not added and not gone:
        print("  无变化")

    # 缺口增量：创建后被删除的记录只表现为新增缺口（内容对账看不见），单独报出
    def _gaps(d):
        nums = {int(k) for k in d if k.isdigit()}
        if not nums:
            return set()
        return {i for i in range(1, max(nums) + 1) if i not in nums}
    cgap, pgap = _gaps(cur), _gaps(prev)
    new_gap = sorted(cgap - pgap)
    filled_gap = sorted(pgap - cgap)
    if new_gap or filled_gap:
        seg = []
        if new_gap:
            seg.append(f"新增缺口 {len(new_gap)} 个: {new_gap}")
        if filled_gap:
            seg.append(f"补齐缺口 {len(filled_gap)} 个: {filled_gap}")
        print("  (缺口) " + " / ".join(seg))

    # 字段级：序号相同但字段变化。旧快照缺字段（如仅 名字/公司/电话）时只比双方都有的字段。
    changed = []
    for k in cur:
        if k not in prev:
            continue
        p, c = prev[k], cur[k]
        d = [(fld, p.get(fld), c.get(fld)) for fld in FLDS
             if fld in p and fld in c and str(p.get(fld)) != str(c.get(fld))]
        if d:
            changed.append((k, d))
    print(f"\n表内他改/字段变化 {len(changed)} 条（含本 agent 当日 update）:")
    for k, d in sorted(changed, key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        seg = "; ".join(f"{fld}: {o!r}→{n!r}" for fld, o, n in d)
        print(f"  ~ 序号{k} {seg}")
    if not changed:
        print("  无字段变化")


def main():
    tok = R.token()
    # 全表读取走 rec_api.fetch_all（单一实现，避免第二份分页逻辑漂移；守卫R）
    rows = R.fetch_all(tok)

    tot = len(rows)
    yes = sum(1 for f in rows if f.get('地址复核') is True)
    no = sum(1 for f in rows if f.get('地址复核') is False)
    emp = tot - yes - no
    print(f"总记录 {tot} | 已勾 {yes} | 明确否 {no} | 未处理 {emp}")

    kidset = {id(f) for f in rows if R.ischild(f)}
    # 顶层/子拆分 + 批量进度：统一由 rec_api.progress_lines 产出（唯一口径，守卫R）
    for l in R.progress_lines(rows):
        print(l)
    # 口径（守卫I）：“现在确认地址的有多少份”存在两种合理口径，两个都报，不推单个数字
    conf_pcs = 0
    for f in rows:
        if f.get('地址复核') is not True:
            continue
        note = str(g(f, '份数备注') or '')
        ds = "".join(ch for ch in note if ch.isdigit())
        conf_pcs += int(ds) if ds else 1
    print(f"地址复核已确认份数: 按记录 {yes} 份 / 按份数备注折算 {conf_pcs} 份（口径不同请指出）")

    nums = []
    for f in rows:
        try:
            nums.append(int(g(f, '序号')))
        except Exception:
            pass
    if nums:
        mx = max(nums)
        miss = [i for i in range(1, mx + 1) if i not in nums]
        print(f"序号 max={mx} | 缺口 {len(miss)} 个: {miss}")

    def norm_phone(s):
        m = re.findall(r'1[3-9]\d{9}', str(s) or "")
        return m[0] if m else None

    def norm_addr(s):
        s = str(s or "")
        s = re.sub(r'1[3-9]\d{9}', '', s)
        s = re.sub(r'[\s,，。、号室楼层栋幢\-]', '', s)
        return s[-18:] if len(s) >= 18 else s

    byp = collections.defaultdict(list)
    bya = collections.defaultdict(list)
    for f in rows:
        info = g(f, '收件信息')
        rec = (g(f, '序号'), g(f, '名字'), g(f, '公司'))
        ph = norm_phone(info)
        if ph:
            byp[ph].append(rec)
        ad = norm_addr(info)
        if ad:
            bya[ad].append(rec)

    dup_ph = {k: v for k, v in byp.items() if len(v) > 1}
    dup_ad = {k: v for k, v in bya.items() if len(v) > 1 and len({x[0] for x in v}) > 1}

    def render(v):
        return " | ".join(f"{a}/{b}/{c}" for a, b, c in v)

    ph_bad = {k: v for k, v in dup_ph.items() if k not in EXPECTED_PHONE}
    ph_exp = {k: v for k, v in dup_ph.items() if k in EXPECTED_PHONE}
    ad_bad = {k: v for k, v in dup_ad.items()
              if frozenset(x[0] for x in v) not in EXPECTED_ADDR_PAIRS}
    ad_exp = {k: v for k, v in dup_ad.items()
              if frozenset(x[0] for x in v) in EXPECTED_ADDR_PAIRS}

    print(f"\n同电话重复 {len(dup_ph)} 组（异常 {len(ph_bad)} / 预期 {len(ph_exp)}）:")
    for k, v in sorted(ph_bad.items()):
        print(f"  [异常] {k}: {render(v)}")
    for k, v in sorted(ph_exp.items()):
        print(f"  [预期] {k}: {render(v)}")

    print(f"\n同地址疑似重复 {len(dup_ad)} 组（异常 {len(ad_bad)} / 预期 {len(ad_exp)}）:")
    for k, v in sorted(ad_bad.items()):
        print(f"  [异常] ...{k}: {render(v)}")
    for k, v in sorted(ad_exp.items()):
        print(f"  [预期] ...{k}: {render(v)}")

    if not ph_bad and not ad_bad:
        print("完整性: 无异常重复行")
    else:
        print(f"完整性: 存在 {len(ph_bad) + len(ad_bad)} 组待核对重复（异常）")

    # 数据质量扫描（2026-09-18 新增）：只报「自相矛盾」与「格式破坏」，不报存量风格差异
    print("\n数据质量扫描:")
    contra = sorted((str(g(f, '序号') or '') for f in rows
                     if id(f) not in kidset and f.get('地址复核') is True
                     and not str(g(f, '收件信息') or '').strip()),
                    key=lambda x: int(x) if x.isdigit() else 0)
    brkln = sorted((str(g(f, '序号') or '') for f in rows
                    if '\n' in str(g(f, '收件信息') or '')),
                   key=lambda x: int(x) if x.isdigit() else 0)
    print(f"  已确认但无收件信息（顶层，矛盾）: {len(contra)} 条 {contra}")
    print(f"  收件信息含换行（格式，建议单行）: {len(brkln)} 条 {brkln}")
    print("  说明:「收件信息首段==名字」不作表级校验——存量表大量记录的名字本身就是签收人，"
          "表级扫描会产出 90+ 条噪声；该规则只在新增/更新写入时校验（rec_api.py warn_format 已归一化）。")

    if '--no-snapshot' not in sys.argv:
        do_snapshot(rows, g)


if __name__ == "__main__":
    main()

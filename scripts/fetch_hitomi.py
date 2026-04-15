"""Hitomi(田中瞳) の全作品をFANZA APIから検索取得する。"""
import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")

API_ID = os.getenv("API_ID")
AFFILIATE_ID = os.getenv("AFFILIATE_ID")


def search(keyword, hits=100, sort="rank", offset=1):
    params = {
        "api_id": API_ID,
        "affiliate_id": AFFILIATE_ID,
        "site": "FANZA",
        "service": "digital",
        "floor": "videoa",
        "hits": hits,
        "sort": sort,
        "keyword": keyword,
        "offset": offset,
        "output": "json",
    }
    r = requests.get("https://api.dmm.com/affiliate/v3/ItemList", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def collect(keyword, total=200):
    """複数ページを取得してHitomi出演作のみ抽出"""
    all_items = []
    seen = set()
    for off in range(1, total, 100):
        data = search(keyword, hits=100, offset=off, sort="rank")
        items = data.get("result", {}).get("items", [])
        if not items:
            break
        for it in items:
            cid = it.get("content_id", "")
            if cid in seen:
                continue
            actresses = [a.get("name", "") for a in it.get("iteminfo", {}).get("actress", [])]
            # Hitomi判定: "Hitomi" か "田中瞳" が含まれる
            joined = " ".join(actresses).lower()
            if "hitomi" in joined or "田中瞳" in " ".join(actresses):
                seen.add(cid)
                all_items.append({
                    "cid": cid,
                    "title": it.get("title", ""),
                    "date": it.get("date", ""),
                    "maker": (it.get("iteminfo", {}).get("maker", [{}])[0].get("name", "") if it.get("iteminfo", {}).get("maker") else ""),
                    "series": (it.get("iteminfo", {}).get("series", [{}])[0].get("name", "") if it.get("iteminfo", {}).get("series") else ""),
                    "actresses": actresses,
                    "genres": [g.get("name", "") for g in it.get("iteminfo", {}).get("genre", [])],
                    "image": it.get("imageURL", {}).get("large", ""),
                })
    return all_items


if __name__ == "__main__":
    results = []
    # 複数の検索語で網羅
    for kw in ["Hitomi", "田中瞳", "hitomi Iカップ", "Hitomi 爆乳"]:
        items = collect(kw, total=300)
        for it in items:
            if it["cid"] not in [r["cid"] for r in results]:
                results.append(it)
    # 日付降順ソート
    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    print(f"TOTAL: {len(results)}")
    out = _root / "scripts" / "hitomi_works.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out}")
    # 抜粋表示
    for r in results[:30]:
        print(f"{r['date'][:10]} | {r['cid']:20} | {r['maker'][:20]:20} | {r['title'][:60]}")

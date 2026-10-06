"""Public data sources, fetched server-side and cached so viewers never hit the APIs directly.
- zcashexplorer.app: getblockchaininfo (value pools, upgrades, chain height)
- Blockchair: chain stats (price, 24 h activity, mempool, fees, nodes) and per-block guessed miner
Blockchair's free tier allows ~1440 requests a day: stats every 5 min (288) and the 24 h miner sample every 30 min
(12 pages x 48 = 576) stay well inside it."""
import json, time, urllib.request

UA = {"user-agent": "sotto-pulse/0.1 (+https://github.com)"}
EXPLORER = "https://mainnet.zcashexplorer.app/api/v1/blockchain-info"
BC = "https://api.blockchair.com/zcash"

def get(url, timeout=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.loads(r.read())

def chain():
    d = get(EXPLORER)
    pools = {p["id"]: float(p.get("chainValue") or 0) for p in d.get("valuePools", [])}
    ups = sorted(({"name": v.get("name"), "height": v.get("activationheight"), "status": v.get("status")}
                  for v in (d.get("upgrades") or {}).values()), key=lambda u: u["height"] or 0)
    return {"height": d.get("blocks"), "supply": float(d["chainSupply"]["chainValue"]), "pools": pools, "upgrades": ups,
            "build": d.get("build")}

def stats():
    d = get(BC + "/stats")["data"]
    return {"price": d.get("market_price_usd"), "price_change_24h": d.get("market_price_usd_change_24h_percentage"),
            "blocks_24h": d.get("blocks_24h"), "tx_24h": d.get("transactions_24h"), "mempool_tx": d.get("mempool_transactions"),
            "median_fee_usd": d.get("median_transaction_fee_usd_24h"), "nodes": d.get("nodes"),
            "hashrate_24h": d.get("hashrate_24h"), "market_cap": d.get("market_cap_usd"), "height": d.get("best_block_height"),
            "best_block_time": d.get("best_block_time")}

import re
# Pool tags pools write into the coinbase input. Blockchair's own guessed_miner names barely a seventh of blocks,
# so the tag is read directly. "Mined by <name>" is a per-user tag several pools use: grouped, not guessed at.
TAGS = [("foundry", "Foundry"), ("luxor", "Luxor"), ("2miners", "2Miners"), ("sluicey", "Sluicey"), ("kupool", "KuPool"),
        ("mined by poolin", "Poolin"), ("viabtc", "ViaBTC"), ("f2pool", "F2Pool"), ("antpool", "AntPool"), ("binance", "Binance Pool")]

def pool_of(b):
    g = (b.get("guessed_miner") or "").strip()
    try: tag = bytes.fromhex(b.get("coinbase_data_hex") or "").decode("latin1").lower()
    except ValueError: tag = ""
    for needle, name in TAGS:
        if needle in tag: return name
    if g and g.lower() != "unknown": return g
    if re.search(r"mined by [a-z0-9]", tag): return "Mined-by user tags"
    return "Untagged"

def miners(blocks=1100):
    """The pool behind each of the last ~24 h of blocks, newest first, 100 per page."""
    out = []
    for off in range(0, blocks, 100):
        page = get(f"{BC}/blocks?limit=100&offset={off}&s=id(desc)")["data"]
        out += [{"h": b["id"], "t": b["time"], "m": pool_of(b)} for b in page]
        time.sleep(1.2)                       # gentle on the free tier
        if len(page) < 100: break
    return out

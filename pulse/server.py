"""Sotto Pulse server: refreshes the sources in the background, serves /api/pulse and the static dashboard."""
import json, os, sqlite3, threading, time, traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from . import sources

PORT = int(os.environ.get("PULSE_PORT", "8930"))
DATA = os.environ.get("PULSE_DATA", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
PUBLIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
NU7_TARGET = os.environ.get("PULSE_NU7_TARGET", "2026-11-05T00:00:00Z")   # announced target; height decided 2026-10-20
SHIELDED = ("ironwood", "orchard", "sapling", "sprout")
STATE = {"chain": None, "stats": None, "miners": None, "t": {}}
lock = threading.Lock()

def db():
    os.makedirs(DATA, exist_ok=True)
    c = sqlite3.connect(os.path.join(DATA, "history.sqlite"), check_same_thread=False)
    c.execute("CREATE TABLE IF NOT EXISTS snap (t INTEGER PRIMARY KEY, height INTEGER, supply REAL, pools TEXT, price REAL)")
    return c
H = db()

def refresher(name, fn, every):
    def run():
        while True:
            try:
                v = fn()
                with lock: STATE[name] = v; STATE["t"][name] = int(time.time())
                if name == "chain":
                    with lock:
                        H.execute("INSERT OR REPLACE INTO snap VALUES (?,?,?,?,?)", (int(time.time()) // 1800 * 1800, v["height"], v["supply"],
                                  json.dumps(v["pools"]), (STATE["stats"] or {}).get("price"))); H.commit()
            except Exception:
                traceback.print_exc()
            time.sleep(every)
    threading.Thread(target=run, daemon=True, name=name).start()

def miner_summary(blocks):
    if not blocks: return None
    n = len(blocks); counts = {}
    for b in blocks: counts[b["m"]] = counts.get(b["m"], 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    known = [(m, c) for m, c in ranked if m not in ("Untagged", "Mined-by user tags", "Unknown")]
    # pools needed to pass half of all blocks (unknown blocks count against nobody)
    acc = k = 0
    for m, c in known:
        acc += c; k += 1
        if acc * 2 > n: break
    else:
        k = None
    return {"blocks": n, "nakamoto": k, "unknown": counts.get("Untagged", 0) + counts.get("Mined-by user tags", 0),
            "top": [{"name": m, "blocks": c, "share": c / n} for m, c in ranked[:8]],
            "first_height": blocks[-1]["h"], "last_height": blocks[0]["h"]}

def pulse():
    with lock:
        ch, st, mi, t = STATE["chain"], STATE["stats"], STATE["miners"], dict(STATE["t"])
        hist = H.execute("SELECT t, pools, supply FROM snap ORDER BY t DESC LIMIT 336").fetchall()
    if not ch: return {"ready": False}
    pools, total = ch["pools"], ch["supply"]
    shielded = sum(pools.get(p, 0) for p in SHIELDED)
    price = (st or {}).get("price")
    return {"ready": True, "height": ch["height"], "supply": total, "price": price,
            "price_change_24h": (st or {}).get("price_change_24h"), "market_cap": (st or {}).get("market_cap"),
            "pools": pools, "shielded": shielded, "shielded_share": shielded / total if total else None,
            "sprout": {"zec": pools.get("sprout", 0), "usd": pools.get("sprout", 0) * price if price else None, "nu7_target": NU7_TARGET},
            "network": st, "mining": miner_summary(mi), "upgrades": ch["upgrades"][-5:],
            "history": [{"t": r[0], "shielded_share": sum(json.loads(r[1]).get(p, 0) for p in SHIELDED) / r[2]} for r in reversed(hist)],
            "updated": t}

TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".png": "image/png"}
class Hd(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, code, body, ctype="application/json"):
        self.send_response(code); self.send_header("content-type", ctype); self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff"); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/api/pulse": return self.send(200, json.dumps(pulse()).encode())
        if p == "/": p = "/index.html"
        f = os.path.normpath(os.path.join(PUBLIC, p.lstrip("/")))
        if not f.startswith(PUBLIC) or not os.path.isfile(f): return self.send(404, b'{"error":"not found"}')
        with open(f, "rb") as fh: self.send(200, fh.read(), TYPES.get(os.path.splitext(f)[1], "application/octet-stream"))

def main():
    refresher("stats", sources.stats, 300)
    refresher("chain", sources.chain, 120)
    refresher("miners", sources.miners, 1800)
    s = ThreadingHTTPServer(("127.0.0.1", PORT), Hd)
    print(f"sotto pulse on 127.0.0.1:{PORT}", flush=True); s.serve_forever()

if __name__ == "__main__":
    main()

"use strict";
const $ = id => document.getElementById(id);
const n0 = x => Math.round(x).toLocaleString();
const usd = x => x == null ? "" : x >= 1e9 ? "$" + (x / 1e9).toFixed(2) + "B" : x >= 1e6 ? "$" + (x / 1e6).toFixed(1) + "M" : "$" + Math.round(x).toLocaleString();
const pct = (x, d = 1) => (x * 100).toFixed(d) + "%";
const POOLS = [["ironwood", "Ironwood", "var(--gold)", 1], ["orchard", "Orchard", "var(--gold2)", 1], ["sapling", "Sapling", "var(--gold3)", 1],
               ["sprout", "Sprout", "var(--gold4)", 1], ["lockbox", "Lockbox", "var(--lock)", 0], ["transparent", "Transparent", "var(--trans)", 0]];
async function load() {
  let d; try { d = await (await fetch("/api/pulse")).json(); } catch (e) { return; }
  if (!d.ready) { setTimeout(load, 3000); return; }
  $("height").textContent = "block " + n0(d.height);
  $("price").textContent = d.price ? "$" + d.price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "...";
  if (d.price_change_24h != null) { const c = d.price_change_24h; $("chg").textContent = (c >= 0 ? "+" : "") + c.toFixed(2) + "% 24 h"; $("chg").className = c >= 0 ? "up" : "down"; }
  $("share").textContent = pct(d.shielded_share); $("shieldedZec").textContent = n0(d.shielded) + " ZEC";
  const m = d.mining;
  if (m) { const top = m.top.find(t => !/^(Untagged|Mined-by user tags|Unknown)$/.test(t.name)), untagged = (m.top.find(t => t.name === "Untagged") || { share: 0 }).share;
    $("nk").textContent = top ? pct(top.share) : "..."; $("nkNote").textContent = (top ? top.name + ", " : "") + pct(untagged, 0) + " untagged"; $("minedBlocks").textContent = n0(m.blocks) + " blocks";
    let acc = 0; $("miners").innerHTML = m.top.map(t => { const half = acc * 2 < m.blocks; acc += t.blocks;
      return `<li class="${half && !/^(Untagged|Mined-by user tags|Unknown)$/.test(t.name) ? "half" : ""}"><span class="nm">${t.name.replace(/[<>&]/g, "")}</span><span class="pc">${pct(t.share)}</span><span class="mb"><i style="width:${(t.share * 100).toFixed(1)}%"></i></span></li>`; }).join(""); }
  const net = d.network || {};
  if (net.blocks_24h) { $("bt").textContent = (86400 / net.blocks_24h).toFixed(0) + " s"; $("b24").textContent = n0(net.blocks_24h) + " blocks 24 h"; }
  $("tx").textContent = net.tx_24h ? n0(net.tx_24h) : "..."; $("mp").textContent = net.mempool_tx != null ? n0(net.mempool_tx) + " tx" : "...";
  $("fee").textContent = net.median_fee_usd != null ? "$" + net.median_fee_usd.toFixed(3) : "..."; $("nodes").textContent = net.nodes ? n0(net.nodes) : "...";
  $("hr").textContent = net.hashrate_24h ? (net.hashrate_24h / 1e9).toFixed(1) + " GSol/s" : "..."; $("mc").textContent = usd(net.market_cap);
  // value pools
  $("supply").textContent = n0(d.supply) + " ZEC";
  $("stack").innerHTML = POOLS.map(([k, , c]) => `<i style="width:${((d.pools[k] || 0) / d.supply * 100).toFixed(2)}%;background:${c}" title="${k}"></i>`).join("");
  $("poolRows").innerHTML = POOLS.filter(([k]) => d.pools[k] != null).map(([k, name, c, sh]) => `<tr><td><span class="sw" style="background:${c}"></span>${name}${sh ? '<span class="tag">shielded</span>' : ""}</td><td>${n0(d.pools[k])}</td><td>${usd(d.pools[k] * (d.price || 0))}</td><td>${pct(d.pools[k] / d.supply)}</td></tr>`).join("");
  // sprout sunset
  $("sproutZec").textContent = n0(d.sprout.zec) + " ZEC"; $("sproutUsd").textContent = d.sprout.usd ? usd(d.sprout.usd) + " still in Sprout" : "";
  const days = Math.max(0, Math.ceil((Date.parse(d.sprout.nu7_target) - Date.now()) / 864e5)); $("days").textContent = days;
  $("dayBar").style.width = Math.max(2, 100 - days / 60 * 100) + "%";
  // upgrades: the last activations, then NU7
  $("ups").innerHTML = d.upgrades.slice(-4).map(u => `<li><i></i><span>${u.name}</span><em>block ${n0(u.height)}</em></li>`).join("") +
    `<li class="next"><i></i><span>NU7, 25 s blocks</span><em>target ${new Date(d.sprout.nu7_target).toLocaleDateString(undefined, { day: "numeric", month: "short" })}</em></li>`;
  // shielded share trend (builds up from first run)
  const h = d.history; if (h.length > 1) { const v = h.map(x => x.shielded_share), lo = Math.min(...v), hi = Math.max(...v), X = i => i * 600 / (v.length - 1), Y = s => 72 - (s - lo) / (hi - lo || 1) * 62;
    const p = v.map((s, i) => (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(s).toFixed(1)).join(" ");
    $("trend").innerHTML = `<path class="a" d="${p} L600 80 L0 80 Z"/><path class="l" d="${p}"/>`; $("trend").classList.add("on"); }
}
load(); setInterval(load, 60000);

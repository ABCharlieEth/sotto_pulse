# Sotto Pulse

A live health dashboard for Zcash: how much ZEC is shielded, the value of every pool, the ZEC still in Sprout ahead of
NU7, which pools mine the blocks, and the network's pace.

- Data: [zcashexplorer.app](https://mainnet.zcashexplorer.app) (`getblockchaininfo`: value pools, upgrades) and
  [Blockchair](https://blockchair.com/zcash) (price, 24 h activity, per-block coinbase tags), fetched server-side and
  cached; a half-hourly snapshot builds the shielded-share history.
- Mining pools are read from the tag each pool writes into the coinbase; untagged blocks are shown as untagged, never
  guessed.
- Python 3 standard library only.

```sh
python3 -m pulse.server      # http://127.0.0.1:8930
```

MIT licensed.

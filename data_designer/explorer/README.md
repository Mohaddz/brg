# BRG conversation explorer

A small React + TypeScript + Vite app built with actual shadcn/ui components.
The production server runs on the VM and reads `../output` in place. Datasets
are never bundled into the frontend. The API is read-only and binds to loopback.

## Open the deployed viewer

From PowerShell in the repository:

```powershell
.\data_designer\explorer\connect.ps1
```

Open http://127.0.0.1:8876/?dataset=saudi_natural_v2_50_selected.jsonl.
The VM service survives logout/reboots; rerun the connection script after a
local reboot or disconnected SSH session. An alternative foreground tunnel:

```bash
ssh -N -o ServerAliveInterval=30 -L 127.0.0.1:8876:127.0.0.1:18766 root@135.181.63.163
```

## Develop

Node 22.12+ or Node 24+ and Python 3.10+ are required. Keep data on the VM;
forward its API to local port 18766 while running the frontend locally:

```bash
ssh -N -L 127.0.0.1:18766:127.0.0.1:18766 root@135.181.63.163
```

In `data_designer/explorer`:

```bash
npm ci
npm run dev
```

For small offline fixture datasets, run `python server.py --data <fixture-dir>`
instead. Vite proxies `/api` to that loopback API. Production:

```bash
npm run build
python server.py
```

The committed systemd unit uses `/usr/bin/python3` and needs no project or
training environment. Install on the VM with:

```bash
cp brg-explorer.service /etc/systemd/system/brg-explorer.service
systemctl daemon-reload
systemctl enable --now brg-explorer
```

## Review behavior

- Search requests/scenarios/topics; filter machine pass/flagged and domain.
- Read selected responses, compare each draft/enhanced pair, and inspect judge
  reasoning. Machine screening and human approval are separate.
- Review the whole conversation or individual messages. Changes save in browser
  localStorage. Export a JSONL backup before changing browsers or clearing storage.
- Import/export uses the existing annotation v1 schema and canonical record SHA256.
  The old viewer's storage key is preserved. Use the same `127.0.0.1:8876` origin
  to retain existing local reviews, or import an earlier annotation export.
- Finished conversation JSONL files appear automatically. Stage files, quarantine,
  annotations, and non-conversation diagnostics are excluded. Dataset rows are
  paginated (100/page), and full records are read from disk only when selected.

The app does not approve data for training or change source datasets.
`../export_hybrid_sft.py` still enforces matching fingerprints, human approval,
machine screening, and family separation.

## Checks

```bash
npm run build
npm run lint
npm test
python -m unittest test_server.py
```

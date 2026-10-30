"""Generate deterministic reference outputs in examples/."""
import csv
import json
from pathlib import Path
from autodyn_ev.simulation import simulate

ROOT = Path(__file__).resolve().parent.parent
out = simulate()
folder = ROOT / 'examples'
folder.mkdir(exist_ok=True)
with (folder/'default_bump_metrics.json').open('w') as f:
    json.dump({'scenario': {'vehicle':out['vehicle'],'road':out['road'],'settings':out['settings']},'metrics':out['metrics'],'assumptions':out['assumptions']}, f, indent=2)
columns = out['channels']
with (folder/'default_bump_response.csv').open('w',newline='') as f:
    writer=csv.writer(f)
    writer.writerow(columns)
    writer.writerows(zip(*columns.values()))
print('Exported',out['samples'],'samples to', folder)

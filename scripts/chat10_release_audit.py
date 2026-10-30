"""Reproducible local release surface and GitHub-preflight audit (stdlib only).

This checks repository contents. It does not create a repo, access accounts or deploy.
"""
import argparse
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PROTECTED=('physics.py','halfcar.py','simulation.py','braking.py','regen.py','optimization.py','analysis.py','ride.py')
SKIP_EXT={'.png','.jpg','.jpeg','.gif','.zip','.pdf','.woff','.webp','.csv','.pyc'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run():
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(c in {'__pycache__','.git','.venv'} for c in p.parts))
    source=[p for p in files if p.suffix in {'.py','.js','.cjs','.html','.css','.toml','.yml'}]
    textual=[p for p in source if p.suffix not in SKIP_EXT]
    findings=[]
    # Precise, non-exhaustive leaked-credential indicators: review before publishing.
    patterns=(re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
              re.compile(r'gh[pousr]_[A-Za-z0-9_]{24,}'),
              re.compile(r'AKIA[0-9A-Z]{16}'),
              re.compile(r'(?i)(?:password|client_secret|access_token|api_key)\s*[:=]\s*[\"\'](?!example|placeholder|test)[^\"\']{12,}[\"\']'))
    for p in textual:
        data=p.read_text(errors='replace')
        for pattern in patterns:
            if pattern.search(data):findings.append({'file':str(p.relative_to(ROOT)),'type':'candidate secret; manual review required'})
    checks={
        'current_pyproject_version': 'version = "1.0.0"' in (ROOT/'pyproject.toml').read_text(),
        'ui_version': 'v1.0 · Session 10' in (ROOT/'web/index.html').read_text(),
        'keyboard_skip_link': 'class="skip-link"' in (ROOT/'web/index.html').read_text(),
        'no_external_script_tags': not re.search(r'<script[^>]+src=["\']https?://', (ROOT/'web/index.html').read_text()),
        'no_mandatory_runtime_dependencies': 'dependencies = []' in (ROOT/'pyproject.toml').read_text(),
        'has_ci': (ROOT/'.github/workflows/ci.yml').is_file(),
        'has_gitignore': (ROOT/'.gitignore').is_file(),
        'no_embedded_private_key_candidates': not findings,
    }
    result={'schema':'chat10-release-audit-1.0','release':'1.0.0','scope':'static local-file audit, not a guarantee against secrets or legal problems',
      'repository_metadata_present': (ROOT/'.git').exists(),
      'files_checked':len(files),'source_files_checked':len(source),'checks':checks,'candidate_secret_findings':findings,
      'protected_files_sha256':{name:sha(ROOT/'autodyn_ev'/name) for name in PROTECTED},
      'known_limitations':['Binary and historical archives not exhaustively inspected for credentials','No license is granted by an absent LICENSE file','No physical vehicle testing','No public deployment has been performed']}
    if not all(checks.values()):raise AssertionError('Release audit failed: '+str(checks)+' findings '+str(findings))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='docs/CHAT10_RELEASE_AUDIT.json');args=p.parse_args()
    report=run();path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2)+'\n')
    print('Release audit:',sum(report['checks'].values()),'/',len(report['checks']),'checks PASS; source files',report['source_files_checked'])

if __name__=='__main__':main()

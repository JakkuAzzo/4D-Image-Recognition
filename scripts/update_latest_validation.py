#!/usr/bin/env python3
"""Update latest_validation.json at repository root based on newest exports/validation_* directory.
Merges validation_manifest.json plus adds build timestamp.
"""
import json, glob, os, time
from pathlib import Path

def newest_validation_dir():
    dirs = glob.glob('exports/validation_*')
    dirs = [d for d in dirs if Path(d).is_dir()]
    if not dirs:
        return None
    dirs.sort(key=lambda d: Path(d).stat().st_mtime, reverse=True)
    return dirs[0]

def main():
    nd = newest_validation_dir()
    latest = {'error': 'no validation directories found'} if not nd else {}
    if nd:
        manifest = Path(nd) / 'validation_manifest.json'
        if manifest.exists():
            try:
                latest = json.loads(manifest.read_text())
            except Exception as e:
                latest = {'error': f'failed to read manifest: {e}'}
        else:
            latest = {'error': 'validation_manifest.json missing in newest directory', 'path': nd}
    latest['generated_at'] = str(int(time.time()))
    Path('latest_validation.json').write_text(json.dumps(latest, indent=2))
    print('latest_validation.json updated')

if __name__ == '__main__':
    main()

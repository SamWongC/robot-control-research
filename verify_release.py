"""Verify the byte-for-byte release inventory without external packages."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent
def main():
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text(encoding='utf8'))
    errors=[]
    for item in manifest['files']:
        path=(ROOT/item['path']).resolve()
        if not path.is_relative_to(ROOT):errors.append('Unsafe path: '+item['path']);continue
        if not path.is_file():errors.append('Missing: '+item['path']);continue
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:errors.append('Changed: '+item['path'])
    for error in errors:print(error)
    print(f"Verified {len(manifest['files'])} inventoried files; {len(errors)} errors. Extra untracked files are not checked.")
    return int(bool(errors))
if __name__=='__main__':sys.exit(main())

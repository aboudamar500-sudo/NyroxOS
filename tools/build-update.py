#!/usr/bin/env python3
import hashlib, json, os, subprocess, tarfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "release-files"
PACKAGES = ["nyroxos-base", "nyroxos-keyring", "nyroxos-update-manager"]
OUT.mkdir(parents=True, exist_ok=True)
deb_files = []
for package in PACKAGES:
    folder = ROOT / "packaging" / package
    subprocess.run(["dpkg-deb", "--build", str(folder), str(OUT)], check=True)
    deb = next(OUT.glob(package + "_*.deb"))
    deb_files.append(deb)
bundle = OUT / "nyroxos-update.tar.gz"
with tarfile.open(bundle, "w:gz") as archive:
    for deb in deb_files:
        archive.add(deb, arcname=deb.name)
parts = []
with bundle.open("rb") as source:
    index = 0
    while True:
        chunk = source.read(100 * 1024 * 1024)
        if not chunk:
            break
        name = f"NyroxOS-update.part-{index:03d}"
        target = OUT / name
        target.write_bytes(chunk)
        parts.append({"name": name, "sha256": hashlib.sha256(chunk).hexdigest()})
        index += 1
def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()
manifest = {
    "version": os.environ.get("GITHUB_RUN_NUMBER", "1.0.0"),
    "packages": [{"name": p.name, "sha256": file_hash(p)} for p in deb_files],
    "bundle": {
        "name": bundle.name,
        "sha256": file_hash(bundle),
        "parts": parts
    }
}
(OUT / "manifest.json").write_text(
    json.dumps(manifest, separators=(",", ":")) + "\n"
)
print("Update bundle and manifest created.")
import base64, tempfile
private_key = os.environ.get("NYROX_UPDATE_SIGNING_KEY")
if not private_key:
    raise SystemExit("Missing NYROX_UPDATE_SIGNING_KEY secret")
with tempfile.NamedTemporaryFile(mode="w", delete=False) as key:
    key.write(private_key)
    key_path = key.name
try:
    raw_sig = OUT / "manifest.sig.raw"
    subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", key_path,
                    "-rawin", "-in", str(OUT / "manifest.json"),
                    "-out", str(raw_sig)], check=True)
    (OUT / "manifest.json.sig").write_bytes(
        base64.b64encode(raw_sig.read_bytes()) + b"\n"
    )
    raw_sig.unlink()
finally:
    os.unlink(key_path)
print("Manifest signed successfully.")

"""Apply the candidate fix only to the exact audited upstream source."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


CONFIG = Path(__file__).resolve().parent.parent


def verify_files(source, manifest, phase):
    for relative, hashes in manifest["files"].items():
        actual = hashlib.sha256((source / relative).read_bytes()).hexdigest()
        expected = hashes[f"{phase}_sha256"]
        if actual != expected:
            raise SystemExit(f"{phase} checksum mismatch: {relative}: {actual}")
        print(f"OK {phase}: {relative}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply_patch.py PATH_TO_UPSTREAM_CHECKOUT")
    source = Path(sys.argv[1]).resolve()
    manifest = json.loads((CONFIG / "manifest.json").read_text(encoding="utf-8"))
    head = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != manifest["upstream_commit"]:
        raise SystemExit(f"Unexpected upstream commit: {head}")
    verify_files(source, manifest, "original")
    command = ["git", "-c", "core.autocrlf=false", "-C", str(source),
               "apply", "--whitespace=error"]
    patch = str(CONFIG / "jit-startup-order.patch")
    subprocess.run([*command, "--check", patch], check=True)
    subprocess.run([*command, patch], check=True)
    verify_files(source, manifest, "patched")
    print(f"Verified JIT patch on upstream {head}")


if __name__ == "__main__":
    main()

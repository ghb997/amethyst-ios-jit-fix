"""Check packaging and compiled patch evidence, not real-device JIT behavior."""

import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import zipfile


APP = "Payload/AngelAuraAmethyst.app/"
MARKER = b"JIT flag set; continuing to JVM script verification"


def verify(path):
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise ValueError(f"ZIP integrity failed: {corrupt}")
        names = set(archive.namelist())
        required = [
            "Info.plist", "AngelAuraAmethyst", "libs/launcher.jar",
            "UniversalJIT26.js", "UniversalJIT26Extension.js",
        ]
        for relative in required:
            name = APP + relative
            if name not in names or archive.getinfo(name).file_size == 0:
                raise ValueError(f"Missing or empty app component: {relative}")
        info = plistlib.loads(archive.read(APP + "Info.plist"))
        if info["CFBundleExecutable"] != "AngelAuraAmethyst":
            raise ValueError("Unexpected main executable")
        binary = archive.read(APP + "AngelAuraAmethyst")
        if MARKER not in binary:
            raise ValueError("The compiled executable does not contain the JIT fix diagnostic")
        runtimes = []
        for version in (8, 17, 21, 25):
            prefix = APP + f"java_runtimes/java-{version}-openjdk/"
            libraries = [name for name in names
                         if name.startswith(prefix) and name.endswith("/libjvm.dylib")
                         and archive.getinfo(name).file_size > 0]
            if not libraries or prefix + "release" not in names:
                raise ValueError(f"Missing full Java {version} runtime")
            runtimes.append(version)
        report = {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "zip_integrity": "passed",
            "compiled_jit_fix_marker": "present",
            "bundle_identifier": info.get("CFBundleIdentifier"),
            "bundle_version": info.get("CFBundleVersion"),
            "bundle_short_version": info.get("CFBundleShortVersionString"),
            "java_runtimes": runtimes,
            "real_device_test": "not performed",
        }
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    report["sha256"] = digest.hexdigest()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    output = json.dumps(verify(args.ipa), indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()

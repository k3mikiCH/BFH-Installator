#!/usr/bin/env python3
# BFH EA patch installer
# Made by k3miki

import xml.etree.ElementTree as ET
import urllib.request as URLREQUEST
import tempfile
import os
import sys
import lzma
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

"""
BFH INSTALLER

"""
import lzma
import os
import struct
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

@dataclass(frozen=True)
class ArchiveEntry:
    name: str
    data_offset: int
    data_length: int


class PatchArchive:
    """Python equivalent of the C# PatchArchive class."""

    def __init__(self, path: str):
        self._stream = open(path, "rb")
        self._entries: Dict[str, ArchiveEntry] = {}
        self._index()

    # ---- public API -----------------------------------------------------

    @property
    def entries(self) -> Dict[str, ArchiveEntry]:
        """Read-only view of the indexed entries, keyed by sanitized name."""
        return self._entries

    def find(self, name: str) -> Tuple[bool, Optional[ArchiveEntry]]:
        """Mirrors TryGet(string name, out ArchiveEntry entry)."""
        entry = self._entries.get(self.sanitize(name))
        return (entry is not None, entry)

    def extract_to(self, entry: ArchiveEntry, destination_path: str) -> int:
        """Decompresses `entry` to `destination_path`, returns bytes written."""
        dest_dir = os.path.dirname(destination_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        self._stream.seek(entry.data_offset)
        header = self._read_exact(13)
        properties = header[0:5]
        output_size = struct.unpack("<q", header[5:13])[0]

        with open(destination_path, "wb") as destination:
            if output_size == 0:
                return 0

            input_size = entry.data_length - len(header)
            compressed = self._read_exact(input_size)

            filt = self._lzma1_filter(properties)
            decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[filt])
            data = decompressor.decompress(compressed, max_length=output_size)
            destination.write(data)

        return output_size

    @staticmethod
    def sanitize(name: str) -> str:
        return name.lstrip("_").replace("..", "") # stop obj poison and path traversal

    def close(self) -> None:
        self._stream.close()

    # context-manager support (Dispose equivalent)
    def __enter__(self) -> "PatchArchive":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ---- internals --------------------------------------------------------

    def _index(self) -> None:
        while True:
            length_byte = self._stream.read(1)
            if not length_byte:
                break  # EOF, equivalent to ReadByte() returning -1

            name_length = length_byte[0]
            name_bytes = self._read_exact(name_length)
            length_header = self._read_exact(5)

            data_length = (
                length_header[0]
                | (length_header[1] << 8)
                | (length_header[2] << 16)
                | (length_header[3] << 24)
                | (length_header[4] << 32)
            )

            name = name_bytes.decode("ascii")
            data_offset = self._stream.tell()
            self._entries[self.sanitize(name)] = ArchiveEntry(name, data_offset, data_length)
            self._stream.seek(data_length, os.SEEK_CUR)

    def _read_exact(self, count: int) -> bytes:
        data = self._stream.read(count)
        if len(data) != count:
            raise EOFError(f"Expected {count} bytes, got {len(data)}")
        return data

    @staticmethod
    def _lzma1_filter(properties: bytes) -> dict:
        """Decodes the 5-byte LZMA1 properties header into a filter spec."""
        d = properties[0]
        lc = d % 9
        d //= 9
        lp = d % 5
        pb = d // 5
        dict_size = struct.unpack("<I", properties[1:5])[0]
        return {
            "id": lzma.FILTER_LZMA1,
            "dict_size": dict_size,
            "lc": lc,
            "lp": lp,
            "pb": pb,
        }

DEFAULT_CDN_URL = "http://static.cdn.ea.com/bfheroes/s/f/eagames/battlefield/bfheroes/patches/build_1.112.250284.0/"

def safe_relative_path(value):
    """Convert manifest paths to safe paths relative to the install folder."""
    value = value.replace("\\\\", "/").lstrip("/")
    parts = [part for part in value.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise ValueError(f"Unsafe path in manifest: {value}")
    return Path(*parts)

def read_ea_manifest(xml_file):
    root = ET.parse(xml_file).getroot()
    file_changes = root.find("FileChanges")
    directory_changes = root.find("DirectoryChanges")
    if file_changes is None or directory_changes is None:
        raise ValueError("Patch XML is missing FileChanges or DirectoryChanges.")
    patch_file_info = {}
    new_folder_info = []
    for file_entry in file_changes.findall("new"):
        patch_filename = file_entry.get("File")
        manifest_path = file_entry.get("Path")
        if not patch_filename or not manifest_path:
            continue
        patch_file_info.setdefault(patch_filename, []).append(manifest_path)
    for file_entry in directory_changes.findall("new"):
        folder_path = file_entry.get("Path")
        if folder_path:
            new_folder_info.append(folder_path)
    return {"patch_file_info": patch_file_info, "new_folder_info": new_folder_info}

def main():
    print("Classic Heroes EA Patch Installer")
    print("Made by k3miki")
    print()
    if len(sys.argv) >= 2:
        cdn_url = sys.argv[1].strip()
    else:
        cdn_url = DEFAULT_CDN_URL
        print("No patch URL supplied; using default:", cdn_url)

    cdn_url = cdn_url.rstrip("/") + "/"
    download_dir = Path(tempfile.mkdtemp(prefix="eapatch_"))
    patch_dir = download_dir / "patches"
    install_dir = download_dir / "install"
    patch_dir.mkdir(parents=True, exist_ok=True)
    install_dir.mkdir(parents=True, exist_ok=True)
    patchxmlfile = download_dir / "patchinfo.xml"

    try:
        print("-- Downloading Patch XML")
        URLREQUEST.urlretrieve(urljoin(cdn_url, "patchinfo.xml"), patchxmlfile)
        patch_info = read_ea_manifest(patchxmlfile)

        print("-- Creating Install Directories")
        for folder_path in patch_info["new_folder_info"]:
            relative = safe_relative_path(folder_path)
            new_folder_path = install_dir / relative
            new_folder_path.mkdir(parents=True, exist_ok=True)
            print("Created:", new_folder_path)

        print("-- Downloading and Extracting Game Files")
        for patch_file, manifest_file_list in patch_info["patch_file_info"].items():
            # Keep downloaded archives inside the patch cache regardless of URL path.
            archive_name = Path(patch_file.replace("\\\\", "/")).name
            if not archive_name:
                print("Skipping invalid patch archive path:", patch_file)
                continue
            archive_path = patch_dir / archive_name
            if archive_path.is_file():
                print("File", archive_path, "exists, not downloading.")
            else:
                print("Downloading", archive_path, "...", end="", flush=True)
                URLREQUEST.urlretrieve(urljoin(cdn_url, patch_file.lstrip("/")), archive_path)
                print("Done!")

            with PatchArchive(str(archive_path)) as patch_archive:
                for manifest_file in manifest_file_list:
                    relative = safe_relative_path(manifest_file)
                    outfile = install_dir / relative
                    print("Extracting", manifest_file, "...", end="", flush=True)
                    found, entry = patch_archive.find(manifest_file)
                    if found and entry is not None:
                        patch_archive.extract_to(entry, str(outfile))
                        print("Done!")
                    else:
                        print("ERROR: file not found in archive:", manifest_file)

        print("\nFiles installed to:", install_dir)
        print("Patch files cached at:", patch_dir)
        print("Made by k3miki")
    except Exception as exc:
        print("\nInstaller error:", exc, file=sys.stderr)
        print("Temporary files are located at:", download_dir, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

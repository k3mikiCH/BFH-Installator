# Classic Heroes EA Patch Installer

A simple Python-based patch downloader and extractor for Battlefield Heroes.

**Made by k3miki — ClassicHeroes**

## Features

- Downloads patch manifests from the EA CDN.
- Supports selecting a game build by editing `main.py`.
- Downloads patch archives and extracts game files.
- Parses `patchinfo.xml`.
- Creates the required directory structure.
- Uses Python's standard library without additional dependencies.

## Requirements

- Python 3.10 or newer recommended.
- An internet connection.
- Enough free disk space for downloaded and extracted files.

## Installation and Usage

### 1. Download the repository

Download the repository from GitHub and extract it, or clone it:

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY_FOLDER
```

### 2. Choose the game version

Open `main.py` in a code editor, such as Visual Studio Code or Notepad.

Find this line:

```python
DEFAULT_CDN_URL = "http://static.cdn.ea.com/bfheroes/s/f/eagames/battlefield/bfheroes/patches/build_1.112.250284.0/"
```

Change `1.112.250284.0` to the build version you want to download.

For example:

```python
DEFAULT_CDN_URL = "http://static.cdn.ea.com/bfheroes/s/f/eagames/battlefield/bfheroes/patches/build_1.126.254667.0/"
```

**Important:** The selected build must exist on the CDN and contain a compatible `patchinfo.xml` manifest and patch archives.

Save `main.py` after editing the URL.

### 3. Run the installer

Open a terminal in the folder containing `main.py` and run:

```bash
py main.py
```

If the `py` command is unavailable, try:

```bash
python main.py
```

### 4. Wait for the extraction to finish

The installer will download the patch manifest, create the required directories, download the referenced archives, and extract the files.

When successful, it displays the output directory:

```text
Files installed to: ...
Patch files cached at: ...
```

## Output Structure

The installer creates a temporary working directory automatically:

```text
eapatch_XXXXXXXX/
├── patchinfo.xml
├── patches/
└── install/
```

- `patchinfo.xml` — downloaded patch manifest.
- `patches/` — downloaded patch archives.
- `install/` — extracted game files.

**Note:** The current version extracts files into a temporary directory rather than directly updating an existing game installation. Copy or preserve the extracted files if you need them after the temporary directory is removed.

## Troubleshooting

**HTTP 404:** Check whether the selected build exists on the EA CDN.

**Download errors:** Check your internet connection and the availability of the patch files.

**Missing archive entries:** The downloaded archive may not match the manifest or may be corrupted.

**Insufficient disk space:** Free up space before running the installer again.

## Disclaimer

This is an independent, non-commercial fan project. It is not affiliated with, endorsed by, or sponsored by Electronic Arts.

Battlefield Heroes and related trademarks and assets belong to their respective owners.

## Credits

**Made by k3miki**

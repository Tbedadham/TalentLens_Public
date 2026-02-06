#!/usr/bin/env python3
"""
Script to download files (images and PDFs) from .webloc files in data/discord/links/
"""

import os
import plistlib
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def extract_url_from_webloc(webloc_path):
    """Extract URL from a macOS .webloc file (plist format)"""
    try:
        with open(webloc_path, 'rb') as f:
            plist_data = plistlib.load(f)
        return plist_data.get('URL')
    except Exception as e:
        print(f"✗ Error reading {webloc_path.name}: {e}")
        return None


KNOWN_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff'}


def get_filename_from_webloc(webloc_path, url):
    """Get a clean filename from the .webloc filename or URL"""
    webloc_name = webloc_path.stem  # Remove .webloc extension

    # Check if the webloc filename has a known file extension (like .pdf or .png)
    ext = os.path.splitext(webloc_name)[1].lower()
    if ext in KNOWN_EXTENSIONS:
        return webloc_name

    # Otherwise, extract the real filename from the URL
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)

    # Clean query params
    if '?' in filename:
        filename = filename.split('?')[0]

    # If URL filename is generic (like "image.png"), prefix with webloc index
    # to avoid collisions
    if filename in ('image.png', 'image.jpg', 'image.jpeg'):
        # Extract a number from the webloc name if possible
        parts = webloc_name.split()
        suffix = parts[-1] if parts else '0'
        name, url_ext = os.path.splitext(filename)
        filename = f"image_{suffix}{url_ext}"

    return filename


def get_file_type(filename):
    """Determine if file is PDF or image based on extension"""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        return 'pdf'
    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        return 'image'
    return 'other'


def download_file(url, output_path):
    """Download file from URL to output path"""
    # Download with proper headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req) as response:
        with open(output_path, 'wb') as out_file:
            out_file.write(response.read())

    return output_path


def main():
    # Define paths
    base_dir = Path(__file__).parent
    links_dir = base_dir / "data" / "discord" / "links"
    base_output_dir = base_dir / "data" / "discord"

    # Create subdirectories for organization
    images_dir = base_output_dir / "images"
    pdfs_dir = base_output_dir / "pdfs"
    images_dir.mkdir(parents=True, exist_ok=True)
    pdfs_dir.mkdir(parents=True, exist_ok=True)

    # Find all .webloc files
    webloc_files = sorted(list(links_dir.glob("*.webloc")))

    if not webloc_files:
        print("No .webloc files found in data/discord/links/")
        return

    print(f"Found {len(webloc_files)} .webloc file(s)\n")

    # Track statistics
    stats = {
        'total': len(webloc_files),
        'downloaded': 0,
        'skipped': 0,
        'failed': 0
    }

    # Process each .webloc file
    for idx, webloc_path in enumerate(webloc_files, 1):
        print(f"[{idx}/{stats['total']}] Processing: {webloc_path.name}")

        try:
            # Extract URL from .webloc file
            url = extract_url_from_webloc(webloc_path)

            if not url:
                print(f"✗ Could not extract URL")
                stats['failed'] += 1
                print()
                continue

            # Get filename and determine file type
            filename = get_filename_from_webloc(webloc_path, url)
            file_type = get_file_type(filename)

            # Determine output directory based on file type
            if file_type == 'pdf':
                output_dir = pdfs_dir
            elif file_type == 'image':
                output_dir = images_dir
            else:
                output_dir = base_output_dir

            output_path = output_dir / filename

            # Skip if already downloaded
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"⊙ Already exists ({file_size:,} bytes): {filename}")
                stats['skipped'] += 1
                print()
                continue

            # Download the file
            print(f"↓ Downloading: {filename}")
            download_file(url, output_path)

            file_size = output_path.stat().st_size
            print(f"✓ Downloaded ({file_size:,} bytes): {filename}")
            stats['downloaded'] += 1

        except Exception as e:
            print(f"✗ Error: {e}")
            stats['failed'] += 1

        print()

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files:      {stats['total']}")
    print(f"Downloaded:       {stats['downloaded']}")
    print(f"Already existed:  {stats['skipped']}")
    print(f"Failed:           {stats['failed']}")
    print(f"\nFiles saved to:")
    print(f"  Images: {images_dir}")
    print(f"  PDFs:   {pdfs_dir}")


if __name__ == "__main__":
    main()

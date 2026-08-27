import gzip
import os
import glob
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "anime.db")
GZ_PATH = os.path.join(DATA_DIR, "anime.db.gz")
CHUNK_SIZE = 60 * 1024 * 1024  # 60 MB chunks (< 100 MB GitHub limit)


def compress_and_split():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found!")
        return

    print(f"Compressing {DB_PATH} -> {GZ_PATH}...")
    with open(DB_PATH, "rb") as f_in:
        with gzip.open(GZ_PATH, "wb", compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)

    gz_size = os.path.getsize(GZ_PATH)
    print(f"Compressed size: {gz_size / (1024*1024):.2f} MB")

    print("Splitting into <60MB chunks for GitHub compatibility...")
    part_num = 0
    with open(GZ_PATH, "rb") as f_in:
        while chunk := f_in.read(CHUNK_SIZE):
            chunk_name = f"{GZ_PATH}.{part_num:02d}"
            with open(chunk_name, "wb") as f_chunk:
                f_chunk.write(chunk)
            print(f"  Created chunk {chunk_name} ({len(chunk) / (1024*1024):.2f} MB)")
            part_num += 1

    # Remove temporary full .gz file since parts are ready
    if os.path.exists(GZ_PATH):
        os.remove(GZ_PATH)
    print(f"Done! Created {part_num} chunks ready for GitHub.")


def restore_db(force: bool = False):
    if os.path.exists(DB_PATH) and not force:
        print(f"{DB_PATH} already exists.")
        return

    parts = sorted(glob.glob(f"{GZ_PATH}.*"))
    if not parts:
        if os.path.exists(GZ_PATH):
            parts = [GZ_PATH]
        else:
            print(f"No archive parts found for {GZ_PATH}")
            return

    print(f"Restoring database from {len(parts)} chunk(s)...")
    temp_gz = os.path.join(DATA_DIR, "anime.db.gz.temp")
    with open(temp_gz, "wb") as f_out:
        for p in parts:
            print(f"  Reading {p}...")
            with open(p, "rb") as f_in:
                shutil.copyfileobj(f_in, f_out)

    print("Decompressing to anime.db...")
    with gzip.open(temp_gz, "rb") as f_in:
        with open(DB_PATH, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    if os.path.exists(temp_gz):
        os.remove(temp_gz)
    print(f"Database restored successfully! Size: {os.path.getsize(DB_PATH)/(1024*1024):.2f} MB")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_db(force=True)
    else:
        compress_and_split()

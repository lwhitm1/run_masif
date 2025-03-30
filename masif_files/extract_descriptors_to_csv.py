import numpy as np
import pandas as pd
from pathlib import Path
import argparse

def load_mapping(mapping_path):
    """Load mapping from 4-digit symlinks to real file names."""
    mapping = {}
    with open(mapping_path) as f:
        for line in f:
            symlink, real = line.strip().split(" -> ")
            mapping[symlink.replace(".pdb", "")] = real.replace(".pdb", "")
    return mapping

def collect_descriptors(output_dir, mapping, use_flipped=False):
    """
    Collect descriptor vectors from MaSIF output folders.
    """
    data = []
    labels = []
    desc_file = "p1_desc_flipped.npy" if use_flipped else "p1_desc_straight.npy"

    for pdb_dir in sorted(Path(output_dir).glob("*")):
        structure_id = pdb_dir.name
        descriptor_path = pdb_dir / "descriptors" / "sc05" / "all_feat" / f"{structure_id}_A" / desc_file

        if descriptor_path.exists():
            try:
                vector = np.load(descriptor_path).flatten()
                real_name = mapping.get(structure_id, structure_id)
                data.append(vector)
                labels.append(real_name)
            except Exception as e:
                print(f"[WARN] Could not load {descriptor_path}: {e}")
        else:
            print(f"[WARN] Missing: {descriptor_path}")

    df = pd.DataFrame(data)
    df.insert(0, "structure", labels)
    return df

def main():
    parser = argparse.ArgumentParser(description="Extract MaSIF descriptors into a CSV file.")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory with masif_output/")
    parser.add_argument("--log_dir", type=str, required=True, help="Directory with pdb_mapping.txt")
    parser.add_argument("--csv_path", type=str, default="masif_descriptors.csv", help="Output CSV file path")
    parser.add_argument("--metadata_csv", type=str, help="Optional metadata CSV to merge on 'structure'")
    parser.add_argument("--use_flipped", action="store_true", help="Use p1_desc_flipped.npy instead of straight")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    log_dir = Path(args.log_dir)
    mapping_path = log_dir / "pdb_mapping.txt"

    if not mapping_path.exists():
        print(f"[ERROR] Mapping file not found: {mapping_path}")
        return

    mapping = load_mapping(mapping_path)
    df = collect_descriptors(output_dir, mapping, use_flipped=args.use_flipped)

    if args.metadata_csv:
        metadata = pd.read_csv(args.metadata_csv)
        df = df.merge(metadata, on="structure", how="left")

    df.to_csv(args.csv_path, index=False)
    print(f"[INFO] Saved descriptor matrix: {args.csv_path}")

if __name__ == "__main__":
    main()


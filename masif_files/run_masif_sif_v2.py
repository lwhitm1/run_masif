import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

def log(message, logfile):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    full_msg = f"{timestamp} {message}"
    print(full_msg)
    with open(logfile, "a") as f:
        f.write(full_msg + "\n")

def create_symlinked_pdb_dir(original_dir, log_dir):
    linked_dir = original_dir.parent / "linked_pdbs"
    os.makedirs(linked_dir, exist_ok=True)
    mapping_file = log_dir / "pdb_mapping.txt"

    with open(mapping_file, "w") as f:
        for idx, pdb_file in enumerate(sorted(original_dir.glob("*.pdb"))):
            new_name = f"{idx+1:04d}.pdb"
            link_path = linked_dir / new_name
            if link_path.exists():
                link_path.unlink()
            link_path.symlink_to(pdb_file.resolve())
            f.write(f"{new_name} -> {pdb_file.name}\n")

    return linked_dir

def create_batch_script(script_path):
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("INPUT_DIR=/workspace/pdbs\n")
        f.write("OUTPUT_DIR=/workspace/outputs\n\n")
        f.write("mkdir -p \"$OUTPUT_DIR\"\n")
        f.write("cd /opt/masif\n")
        f.write("for pdb_file in \"$INPUT_DIR\"/*.pdb; do\n")
        f.write("    filename=$(basename \"$pdb_file\")\n")
        f.write("    pdbid=\"${filename%.pdb}\"\n")
        f.write("    echo \"[INFO] Processing $pdbid...\"\n")
        f.write("    ./preprocess_pdb.sh \"$pdb_file\" \"${pdbid}_A\" -o \"$OUTPUT_DIR/$pdbid\"\n")
        f.write("done\n")
    os.chmod(script_path, 0o755)

def main():
    parser = argparse.ArgumentParser(description="Run MaSIF-NeoSurf preprocessing using an Apptainer .sif container.")
    parser.add_argument("--pdb_dir", type=str, required=True, help="Directory with PDB files")
    parser.add_argument("--output_dir", type=str, default="masif_output", help="Output directory")
    parser.add_argument("--log_dir", type=str, default="logs", help="Log directory")
    parser.add_argument("--sif", type=str, default="/projects/liwh2139/masif/masif-neosurf.sif", help="Path to .sif image")
    args = parser.parse_args()

    pdb_dir = Path(args.pdb_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    log_dir = Path(args.log_dir).resolve()
    sif_path = Path(args.sif).resolve()
    script_path = pdb_dir.parent / "batch_preprocess.sh"
    launcher_log = log_dir / "masif_launcher.log"
    run_log = log_dir / "masif_run.log"

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    if not pdb_dir.exists():
        log(f"[ERROR] PDB directory not found: {pdb_dir}", launcher_log)
        return

    log("Creating symlinked PDB directory...", launcher_log)
    linked_pdb_dir = create_symlinked_pdb_dir(pdb_dir, log_dir)

    log("Creating batch preprocessing script...", launcher_log)
    create_batch_script(script_path)

    log("Running Apptainer container...", launcher_log)
    with open(run_log, "w") as log_file:
        subprocess.run([
            "singularity", "exec",
            "--bind", f"{linked_pdb_dir}:/workspace/pdbs",
            "--bind", f"{output_dir}:/workspace/outputs",
            "--bind", f"{script_path}:/workspace/batch_preprocess.sh",
            str(sif_path),
            "bash", "/workspace/batch_preprocess.sh"
        ], stdout=log_file, stderr=subprocess.STDOUT)

    log("Finished processing.", launcher_log)
    log(f"Launcher log: {launcher_log}", launcher_log)
    log(f"Run log: {run_log}", launcher_log)

if __name__ == "__main__":
    main()


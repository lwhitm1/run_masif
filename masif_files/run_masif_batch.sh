#!/bin/bash
#SBATCH --account=ucb-general
#SBATCH --job-name=masif-preprocess
#SBATCH --partition=atesting        # Change if to amilan for full production runs, if need be add #SBATCH --qos=long if runs will be longer than 24hrs
#SBATCH --nodes=1
#SBATCH --time=01:00:00		    # Change for full production run
#SBATCH --output=/scratch/alpine/%u/masif_runs/%x_%j.out
#SBATCH --error=/scratch/alpine/%u/masif_runs/%x_%j.err

# Load required modules
module purge
module load singularity

# source your conda env
# conda activate env_name

# Set directories
if [ -z "$1" ]; then
  echo "[ERROR] You must provide the PDB directory as the first argument."
  echo "Usage: sbatch run_masif_batch.slurm <pdb_dir> [base_dir]"
  exit 1
fi

PDB_DIR=$(realpath "$1")
SCRATCH_DIR="/scratch/alpine/$USER"
BASE_DIR=${2:-"$SCRATCH_DIR/masif_runs"}
OUT_DIR="$BASE_DIR/masif_output"
LOG_DIR="$BASE_DIR/logs"
SIF_PATH="/projects/liwh2139/masif/masif-neosurf.sif"

# Make sure output folders exist
mkdir -p "$OUT_DIR" "$LOG_DIR"

# Echo paths for confirmation
echo "PDB directory:     $PDB_DIR"
echo "Output directory: $OUT_DIR"
echo "Log directory:    $LOG_DIR"
echo "SIF path:         $SIF_PATH"

# Run the wrapper Python script
python3 /projects/liwh2139/masif/run_masif_sif_v2.py \
  --pdb_dir "$PDB_DIR" \
  --output_dir "$OUT_DIR" \
  --log_dir "$LOG_DIR" \
  --sif "$SIF_PATH"


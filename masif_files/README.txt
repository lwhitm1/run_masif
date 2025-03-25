Everything should be setup to run on alpine.
You'll need to copy the run_masif_batch.sh script from my projects directory:
	cp /projects/liwh2139/masif/run_masif_batch.sh </path/where/you/want/it/>

What the submission script contains:
	Slurm directives:
		#SBATCH --account=ucb-general
		#SBATCH --job-name=masif-preprocess
		#SBATCH --partition=atesting        
		#SBATCH --nodes=1
		#SBATCH --time=01:00:00		    
		#SBATCH --output=/scratch/alpine/%u/masif_runs/%x_%j.out
		#SBATCH --error=/scratch/alpine/%u/masif_runs/%x_%j.err

	** You'll want to change the partition to amilan and the time will depend on how many structures you'll process (it takes ~2-3 minutes). It is currently set to run on the atesting partition for 1 hr.
		* If working with really large datasets, you'll want to add #SBATCH --qos long for jobs that will take longer than 24hrs

	Modules:

		# Load required modules
		module purge
		module load singularity

	** Clears out anything that may have previously been loaded and loads singularity to run the .sif container

	Conda:

		# source your conda env
		# conda activate env_name

	**The script requires python, so any environment you have that has some version of python 3 will work. Just uncomment the conda activte line and list your environment name in place of env_name.

	Directory organization:

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

	**The only mandatory thing you have to declare is the path to the directory where you have the structures/pdbs. When submitting to slurm you run 

		sbatch run_masif_batch.sh <path/to/structs/directory/

	You could also declare the output and log dirs but the default is set to write to scratch. It will create a parent directory called masif_runs and within that directory you'll find all the files.

	Running the python wrapper:

		# Run the wrapper Python script
		python3 /projects/liwh2139/masif/run_masif_sif_v2.py \
		  --pdb_dir "$PDB_DIR" \
		  --output_dir "$OUT_DIR" \
		  --log_dir "$LOG_DIR" \
		  --sif "$SIF_PATH"

	** The script will take the pdb directory and loop through and run all the structures through the precompute stages of the masif neosurf protocol. 
		* masif only accepts files with 4-digit ids/pdb like codes. The script will simlink the input pdbs and mask the original names with 4-digit numerical codes. It is set up to run on chain A of the protein.


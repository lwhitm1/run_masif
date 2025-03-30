#!/usr/bin/env python3

import pyrosetta
import os
import argparse
import pandas as pd
import sys
import datetime
from pyrosetta.rosetta.core.pack.task import TaskFactory
from pyrosetta.rosetta.core.pack.task import operation
from pyrosetta.rosetta.protocols import minimization_packing as pack_min

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Repack side chains for all PDBs in a directory without backbone changes.")
    parser.add_argument("-p", "--pdb_directory", type=str, required=True, help="Directory containing PDB files to process.")
    parser.add_argument("-o", "--output_directory", type=str, required=True, help="Directory to save repacked structures.")
    parser.add_argument("-c", "--csv_file", type=str, default="./pack_score_log.csv", help="CSV file to save score results.")
    parser.add_argument("-n", "--cycles", type=int, default=3, help="Number of repacking cycles (default: 3)")
    return parser.parse_args()

def setup_logging():
    """Redirect stdout and stderr to a log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = f"packing_log_{timestamp}.txt"
    sys.stdout = open(log_file, "w")
    sys.stderr = sys.stdout
    print(f"Logging output to {log_file}\n")

def setup_packer():
    tf = TaskFactory()
    tf.push_back(operation.InitializeFromCommandline())  # Initialize with Rosetta command-line options
    tf.push_back(operation.IncludeCurrent())  # Include current rotamer states
    tf.push_back(operation.NoRepackDisulfides())  # Keep disulfide bonds intact
    tf.push_back(operation.RestrictToRepacking())  # Allow only repacking, no design

    packer = pack_min.PackRotamersMover()
    packer.task_factory(tf)
    
    return packer

def repack_pose(pose, scorefxn, packer, cycles):
    best_pose = pose.clone()
    best_score = scorefxn(pose)

    for i in range(cycles):
        print(f"Running repacking cycle {i+1}/{cycles}...")
        packer.apply(pose)

        # Score the current pose
        current_score = scorefxn(pose)
        print(f"Cycle {i+1} score: {current_score}")

        # Keep the lowest-energy structure
        if current_score < best_score:
            best_score = current_score
            best_pose = pose.clone()
            print(f"New best score found: {best_score}")

    return best_pose, best_score

def main():
    args = parse_args()
    setup_logging()  # Start logging

    # Initialize PyRosetta
    pyrosetta.init("-ignore_unrecognized_res 1 -ex1 -ex2aro")

    # Ensure output directory exists
    os.makedirs(args.output_directory, exist_ok=True)

    # Load optimized scoring function
    scorefxn = pyrosetta.create_score_function("ref2015")

    # Setup the packer (initialized once for efficiency)
    packer = setup_packer()

    # Prepare a list to store score results
    score_data = []

    # Loop through all PDB files in the directory
    for pdb_file in os.listdir(args.pdb_directory):
        if pdb_file.endswith(".pdb"):  # Process only PDB files
            pdb_path = os.path.join(args.pdb_directory, pdb_file)
            print(f"\nProcessing {pdb_file} with {args.cycles} repacking cycles...")

            # Load the PDB file into a pose
            pose = pyrosetta.pose_from_file(pdb_path)

            # Compute initial score
            original_score = scorefxn(pose)
            print(f"Original pose score: {original_score}")

            # Apply repacking and keep the lowest-energy structure
            best_pose, best_score = repack_pose(pose, scorefxn, packer, args.cycles)

            # Save the best structure to PDB
            output_file = os.path.join(args.output_directory, f"best_packed_{pdb_file}")
            best_pose.dump_pdb(output_file)
            print(f"Lowest-energy structure saved as {output_file}")

            # Store score data for CSV
            score_data.append({
                "PDB File": pdb_file,
                "Original Score": original_score,
                "Best Packed Score": best_score,
                "Δ Score (Repacking)": best_score - original_score
            })

    # Save score data to CSV
    df = pd.DataFrame(score_data)
    df.to_csv(args.csv_file, index=False)
    print(f"\nAll PDBs have been processed! Score results saved to {args.csv_file}.")

if __name__ == "__main__":
    main()
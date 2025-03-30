import os
import shutil
import glob
import argparse

def create_commands(AF2_input_directory, output_cmd_directory, output_structure_directory):
    # Ensure the output directories exist
    os.makedirs(output_cmd_directory, exist_ok=True)
    os.makedirs(output_structure_directory, exist_ok=True)

    # Get full path for AF2 inputs
    AF2_input_directory = os.path.abspath(AF2_input_directory)

    # Iterate through all FASTA files in the directory
    for fasta_file_path in glob.glob(os.path.join(AF2_input_directory, '*.fasta')):
        # Get the base name without extension
        fasta_file_base = os.path.splitext(os.path.basename(fasta_file_path))[0]

        # Create a subdirectory for the molecule inside the structure directory
        molecule_dir = os.path.join(output_structure_directory, fasta_file_base)
        os.makedirs(molecule_dir, exist_ok=True)

        # Copy the FASTA file to its new subdirectory
        fasta_dest_path = os.path.join(molecule_dir, os.path.basename(fasta_file_path))
        shutil.copy2(fasta_file_path, fasta_dest_path)

        # Create the AlphaFold2 command script and save it in the output commands directory
        command_script_path = os.path.join(output_cmd_directory, f"{fasta_file_base}_AF2.sh")

        commands = [
            "#!/bin/bash\n",
            "#SBATCH --account=ucb-general",
            "#SBATCH --partition=aa100",
            "#SBATCH --output=test.%j.out",
            "#SBATCH --time=00:20:00",
            "#SBATCH --nodes=1",
            "#SBATCH --ntasks=10",
            "#SBATCH --gres=gpu:1",
            "\n",
            "module purge",
            "module load alphafold",
            "\n",
            f"cd {molecule_dir}",
            "\n",
            f'run_alphafold -d $CURC_AF_DBS -o {molecule_dir} -f {os.path.basename(fasta_file_path)} -t 2023-10-10 -m "monomer" -g true -p true'
        ]

        # Write the command script
        with open(command_script_path, 'w') as file:
            file.write("\n".join(commands))

        # Make the script executable
        os.chmod(command_script_path, 0o755)

        print(f"Setup completed for {fasta_file_base}.")
        print(f"   - FASTA copied to: {fasta_dest_path}")
        print(f"   - Command script saved to: {command_script_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AlphaFold2 commands with organized directory structure.")
    parser.add_argument("-i", "--input_directory", help="Path to directory containing FASTA files.")
    parser.add_argument("-c", "--command_output_directory", help="Path to output directory for generated AlphaFold2 command scripts.")
    parser.add_argument("-o", "--structure_output_directory", help="Path to directory where structured FASTA subdirectories will be created.")

    args = parser.parse_args()
    create_commands(args.input_directory, args.command_output_directory, args.structure_output_directory)


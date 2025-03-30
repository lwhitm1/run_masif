"""
Usage example:
python csv_to_fasta.py --fasta_file </path/to/base/seq/fasta> --input_csv </path/to/mutation/csv> --output_dir <output directory> --output_csv <output csv>
"""


import os
import csv
import re
import string
from Bio import SeqIO

# Step 1: Read Sequence from FASTA
def read_fasta_sequence(fasta_file):
    with open(fasta_file, "r") as handle:
        record = next(SeqIO.parse(handle, "fasta"))
        return list(str(record.seq))  # Convert to list for easy mutation application

# Step 2: Parse CSV and Store Mutations
def parse_mutations_from_csv(csv_file):
    with open(csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        headers = csv_reader.fieldnames

        if "Chemical" not in headers:
            raise ValueError("The CSV file must contain a 'Chemical' column.")

        # Identify mutation columns (e.g., "K59", "R120")
        mutation_columns = {}
        for header in headers:
            match = re.match(r"([A-Z])(\d+)", header)
            if match:
                position = int(match.group(2)) - 1  # Convert 1-based to 0-based index
                mutation_columns[header] = position

        # Read mutations from each row
        mutations_data = []
        for row in csv_reader:
            chemical_name = row["Chemical"].strip()
            if not chemical_name:
                continue

            mutations = {}
            for col, pos in mutation_columns.items():
                if row[col]:  # Ensure mutation is not empty
                    mutations[pos] = row[col]  # Map mutation to sequence index

            mutations_data.append({"Chemical": chemical_name, "Mutations": mutations})

    return mutations_data, mutation_columns

# Step 3: Apply Mutations to Sequence
def apply_mutations(base_sequence, mutations):
    mutated_sequence = base_sequence.copy()

    for pos, new_res in mutations.items():
        if 0 <= pos < len(mutated_sequence):  # Ensure valid mutation position
            mutated_sequence[pos] = new_res
        else:
            print(f"Warning: Mutation position {pos+1} is out of range for sequence length {len(mutated_sequence)}.")

    return mutated_sequence

# Step 4: Sanitize File Names
def sanitize_filename(name):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in name if c in valid_chars).replace(" ", "_")

# Step 5: Process Everything & Generate CSV
def process_mutations(fasta_file, input_csv_file, output_dir, output_comparison_csv):
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Read sequence from FASTA
    base_sequence = read_fasta_sequence(fasta_file)
    print(f"Base sequence extracted ({len(base_sequence)} residues): {''.join(base_sequence)}")

    # Step 2: Read mutations from CSV
    mutations_data, mutation_columns = parse_mutations_from_csv(input_csv_file)

    # Prepare the comparison CSV
    sequence_comparison = []

    # First row in CSV: Wild-type sequence
    wild_type_row = ["Wild-Type"] + base_sequence
    sequence_comparison.append(wild_type_row)

    for entry in mutations_data:
        chemical_name = sanitize_filename(entry["Chemical"])
        mutations = entry["Mutations"]

        # Step 3: Apply mutations to sequence
        mutated_sequence = apply_mutations(base_sequence, mutations)
        print(f"Mutated sequence for {chemical_name}: {''.join(mutated_sequence)}")

        # Step 4: Save mutated sequence as a new FASTA file
        mutated_fasta_file = os.path.join(output_dir, f"{chemical_name}.fasta")
        with open(mutated_fasta_file, "w") as f:
            f.write(f">{chemical_name}\n{''.join(mutated_sequence)}\n")
        print(f"Mutated FASTA written to: {mutated_fasta_file}")

        # Add mutated sequence to the comparison table
        sequence_comparison.append([chemical_name] + mutated_sequence)

    # Write comparison CSV file
    with open(output_comparison_csv, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        header = ["Chemical"] + [f"{i+1}" for i in range(len(base_sequence))]
        csv_writer.writerow(header)  # Write column headers
        csv_writer.writerows(sequence_comparison)  # Write sequence data

    print(f"Comparison CSV written to: {output_comparison_csv}")
    print("Processing complete.")

# Step 6: Command-Line Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process mutations and generate mutated FASTA and comparison CSV files.")
    parser.add_argument("-f", "--fasta_file", required=True, help="Path to the input FASTA file.")
    parser.add_argument("-i", "--input_csv", required=True, help="Path to the input CSV file containing mutations.")
    parser.add_argument("-o", "--output_dir", required=True, help="Directory to save the mutated FASTA files.")
    parser.add_argument("-c", "--output_csv", required=True, help="Path to save the sequence comparison CSV file.")

    args = parser.parse_args()

    # Run processing
    process_mutations(args.fasta_file, args.input_csv, args.output_dir, args.output_csv)

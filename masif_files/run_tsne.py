import pandas as pd
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run t-SNE on MaSIF descriptors.")
    parser.add_argument('-i','--input_csv', type=str, required=True, help='CSV file with descriptors')
    parser.add_argument('-o', '--output_prefix', type=str, default='tsne_output', help='Prefix for output files')
    parser.add_argument('-p', '--perplexity', type=float, default=20.0, help='Perplexity for t-SNE (must be < num samples)')
    parser.add_argument('-n', '--n_iter', type=int, default=1000, help='Number of iterations for t-SNE')
    args = parser.parse_args()

    # Load input descriptor data
    df = pd.read_csv(args.input_csv)
    if 'structure' not in df.columns:
        raise ValueError("Input CSV must have a 'structure' column.")

    # Split features and fill missing values
    features = df.drop(columns=['structure']).fillna(0)
    structures = df['structure']

    if args.perplexity >= len(features):
        raise ValueError(f"Perplexity ({args.perplexity}) must be < number of samples ({len(features)}).")

    # Run t-SNE
    tsne = TSNE(n_components=2, perplexity=args.perplexity, n_iter=args.n_iter, random_state=42)
    coords = tsne.fit_transform(features)

    # Save results
    result_df = pd.DataFrame({'x': coords[:, 0], 'y': coords[:, 1], 'structure': structures})
    result_df.to_csv(f"{args.output_prefix}.csv", index=False)

    # Plot
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=result_df, x='x', y='y', s=40, alpha=0.8)
    plt.title("t-SNE of MaSIF Descriptors")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(f"{args.output_prefix}.png", dpi=300)

    print(f"[INFO] t-SNE complete. Saved to {args.output_prefix}.csv and .png")

if __name__ == "__main__":
    main()

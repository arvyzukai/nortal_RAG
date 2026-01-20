
import argparse
import os
from dotenv import load_dotenv

# Import internal modules directly
from app.ingest import ingest_data
from scripts.evaluate import run_evaluation

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Run RAG Experiment (Ingest + Eval)")
    parser.add_argument("--name", required=True, help="Experiment Name (e.g., 'baseline', 'chunk_500')")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    parser.add_argument("--json-path", default="data/scraped_data.json", help="Path to input JSON data")
    args = parser.parse_args()

    print(f"=== Starting Experiment: {args.name} ===")
    print(f"Data source: {args.json_path}")
    
    # Set LangSmith Project Name for this session (globally for this process)
    # This groups traces under this project
    os.environ["LANGCHAIN_PROJECT"] = f"nortal-rag-{args.name}"
    print(f"LangChain Project: {os.environ['LANGCHAIN_PROJECT']}")

    # 1. Ingest
    print("\n[Step 1] Ingesting Data...")
    ingest_data(
        json_path=args.json_path,
        chunk_size=args.chunk_size, 
        chunk_overlap=args.chunk_overlap
    )

    # 2. Evaluate
    print("\n[Step 2] Running Evaluations...")
    
    # Factual
    # Factual
    factual_results = run_evaluation(
        dataset_name="Nortal RAG Factual", 
        experiment_prefix=f"{args.name}-factual"
    )
    
    # Abstract
    abstract_results = run_evaluation(
        dataset_name="Nortal RAG Abstract",
        experiment_prefix=f"{args.name}-abstract"
    )

    print("\n=== Experiment Summary ===")
    
    def print_results(title, results):
        print(f"\n--- {title} ---")
        if not results:
             print("No results found.")
             return
        
        # results is an ExperimentResultRow iterator/list
        try:
             count = 0
             total_score = 0
             metric_name = "Score"
             
             # Iterate over the results
             for r in results:
                 count += 1
                 # Each result has evaluation_results -> dict of key/score
                 # We look for 'correctness' or 'quality'
                 evals = r.get("evaluation_results", {}).get("results", [])
                 for e in evals:
                     if e.key in ["correctness", "quality"]:
                         total_score += e.score or 0
                         metric_name = e.key
             
             if count > 0:
                 avg = total_score / count
                 print(f"Count: {count}")
                 print(f"Average {metric_name.capitalize()}: {avg:.2f}")
             else:
                 print("No evaluated examples found.")
                 
             # Try to print URL from the first result if available or just generic
             if hasattr(results, "experiment_name"):
                 print(f"Experiment: {results.experiment_name}")
        except Exception as e:
             print(f"Could not parse stats: {e}")
             # print(results) # debug if needed

    print_results("Factual Results", factual_results)
    print_results("Abstract Results", abstract_results)

    print("\n=== Experiment Complete ===")
    print("Detailed traces are available in LangSmith.")

if __name__ == "__main__":
    main()

import argparse
import subprocess
import os
import time
import json
from datetime import datetime

def run_command(command):
    """Run a shell command and return output."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=False, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        return result
    except Exception as e:
        print(f"Failed to run command: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Run RAG Experiment")
    parser.add_argument("--name", required=True, help="Experiment Name")
    parser.add_argument("--chunk-size", required=True, type=int)
    parser.add_argument("--chunk-overlap", required=True, type=int)
    args = parser.parse_args()

    print(f"--- Starting Experiment: {args.name} ---")
    start_time = time.time()

    # 1. Ingest Data
    print("\n[Step 1] Ingesting Data...")
    ingest_cmd = f'.\\.venv\\Scripts\\python.exe app\\ingest.py --chunk-size {args.chunk_size} --chunk-overlap {args.chunk_overlap}'
    ingest_res = run_command(ingest_cmd)
    if ingest_res.returncode != 0:
        print("Ingestion failed!")
        print(ingest_res.stderr)
        return

    # 2. Run Factual Evaluation
    print("\n[Step 2] Running Factual Evaluation...")
    # Using pytest and capturing output
    factual_cmd = '.\\.venv\\Scripts\\python.exe -m pytest tests\\evaluation\\test_factual.py'
    factual_res = run_command(factual_cmd)
    
    # Simple parse of pytest output for summary
    factual_score = "N/A"
    if "passed" in factual_res.stdout:
        # Crude parsing logic, valid for now
        # Example: "2 failed, 6 passed in 15.81s"
        try:
            line = [l for l in factual_res.stdout.split('\n') if "passed" in l or "failed" in l][-1]
            factual_score = line.strip()
        except:
            pass
    elif "passed" not in factual_res.stdout and "failed" not in factual_res.stdout:
         # Check if it failed completely
         if "collected" in factual_res.stdout and "items" in factual_res.stdout: 
             # likely all passed or all failed without summary line in short capture? 
             # Pytest usually prints summary.
             pass
    
    if factual_res.returncode != 0:
        print("Factual tests had failures (expected behavior).")

    # 3. Run Abstract Evaluation
    print("\n[Step 3] Running Abstract Evaluation...")
    abstract_cmd = '.\\.venv\\Scripts\\python.exe -m tests.evaluation.run_abstract_eval'
    abstract_res = run_command(abstract_cmd)
    
    abstract_score = "N/A"
    # Parse the output for score (assuming the script prints it)
    # The script prints "Score: X/10" for each q. We could calculate average here or just store the log.
    # For now, let's just mark it as "Ran".

    # 4. Log Results
    log_file = "experiments/experiment_log.txt"
    os.makedirs("experiments", exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | Name: {args.name} | Chunk: {args.chunk_size}/{args.chunk_overlap} | Factual: {factual_score}\n"
    
    with open(log_file, "a") as f:
        f.write(log_entry)
        
    print(f"\nExperiment Complete. Logged to {log_file}")
    print(f"Factual Result: {factual_score}")
    
    # Save detailed logs
    run_dir = f"experiments/runs/{args.name}"
    os.makedirs(run_dir, exist_ok=True)
    with open(f"{run_dir}/factual_log.txt", "w", encoding='utf-8') as f:
        f.write(factual_res.stdout)
    with open(f"{run_dir}/abstract_log.txt", "w", encoding='utf-8') as f:
        f.write(abstract_res.stdout)

if __name__ == "__main__":
    main()

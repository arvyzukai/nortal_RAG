
import json
import os
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def upload_dataset(filename, dataset_name, description, input_keys, output_keys):
    client = Client()
    file_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Processing dataset: {dataset_name}...")
    
    if client.has_dataset(dataset_name=dataset_name):
        print(f"Dataset '{dataset_name}' already exists. Deleting to ensure clean slate.")
        client.delete_dataset(dataset_name=dataset_name)
        
    print(f"Creating dataset '{dataset_name}'...")
    dataset = client.create_dataset(
        dataset_name=dataset_name, 
        description=description
    )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    inputs = []
    outputs = []

    for item in data:
        inputs.append({k: item.get(k) for k in input_keys})
        outputs.append({k: item.get(k) for k in output_keys})

    # In a real production script we might check for duplicates, 
    # but for this "set up the experiments" phase, simpler is better.
    # We rely on the user to keep the JSONs clean.
    client.create_examples(
        inputs=inputs,
        outputs=outputs,
        dataset_id=dataset.id
    )
    print(f"Uploaded {len(inputs)} examples to '{dataset_name}'.")

def main():
    # 1. Factual
    upload_dataset(
        filename="factual_questions.json",
        dataset_name="Nortal RAG Factual",
        description="Factual questions with exact or contains match criteria.",
        input_keys=["question"],
        output_keys=["expected_answer", "match_type"]
    )

    # 2. Abstract
    upload_dataset(
        filename="abstract_questions.json",
        dataset_name="Nortal RAG Abstract",
        description="Abstract questions requiring an LLM judge.",
        input_keys=["question"],
        output_keys=["reference_answer"]
    )

    print("\nDatasets ready in LangSmith.")

if __name__ == "__main__":
    main()

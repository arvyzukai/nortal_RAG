# RAG Optimization Log

## Experiment 1: Baseline
- **Params**: Chunk 1000 / Overlap 200
- **Factual**: 6/8 Passed
- **Failures**:
    1. Experts (Expected 2700)
    2. Acquire 2024 (Expected 3DOT)

## Experiment 2: Small Chunk
- **Params**: Chunk 500 / Overlap 50
- **Factual**: 6/8 Passed
- **Failures**:
    1. Experts (Expected 2700)
    2. Founded (Expected "25 years ago") -> **Regression**
- **Success**:
    - **Fixed "Acquire 2024" (3DOT)**.
- **Insight**: Small chunks help isolate specific proper nouns (3DOT) but may lose context for "founded 25 years ago".

## Experiment 3: Large Chunk
- **Params**: Chunk 2000 / Overlap 400
- **Factual**: 6/8 Passed
- **Failures**: Same as Baseline.
- **Insight**: Larger context didn't help retrieval of the specific acquisition fact.

## Conclusion
**Small Chunking (500/50)** is promising for specific entity retrieval.
The "Founded" regression might be due to valid context splitting.
**Recommendation**: Adopt Small Chunk strategy if "Specific Facts" are priority, or find a middle ground (e.g. 700/100).

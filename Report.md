# RAG Optimization Report

> Tracking experiments to improve Nortal RAG system performance.

## Current Best: Experiment 4
- **Factual Correctness**: 0.88 | **Abstract Quality**: 0.60

---

## Experiments

### Exp 4 — LLM Digestion (2026-01-20)
| Parameter | Value |
|-----------|-------|
| Source | **LLM Digested** (GPT-4o) |
| Sample | 25 pages (20 HTML + 5 PDF) |
| Chunks | 890 (from 171 digested) |
| Chunk Size | 1000 |

**Results**:
- **Factual Correctness**: **0.88** (7/8) ✅
- **Abstract Quality**: 0.60 (6 samples)

**Notes**:
- **Significant Improvement**: +13% factual accuracy vs Exp 2 baseline (0.75).
- **Method**: Pre-processed content with GPT-4o to extract Summary + Key Facts + Topics.
- **Rich Semantics**: Structured summaries provided better retrieval signals than raw chunks.

**LangSmith**: [Factual](https://smith.langchain.com/o/05bea788-b744-53cc-a55e-8f72f5bd94bb/datasets/4274bae4-4b4e-47b8-beff-875df22f77f0/compare?selectedSessions=5f1bb727-1bb8-4496-b00d-f0da9b83dfa8) | [Abstract](https://smith.langchain.com/o/05bea788-b744-53cc-a55e-8f72f5bd94bb/datasets/8b3f3d64-f35f-4cc1-b2ac-4977c00eb9b1/compare?selectedSessions=522d8601-b642-4e77-8b6d-6c4f36bfb377)

---

### Exp 3 — PDF & Expanded Coverage (2026-01-20)
| Parameter | Value |
|-----------|-------|
| max_pages | 200 |
| max_depth | 3 |
| chunk_size | 1000 |
| chunk_overlap | 200 |
| **PDF scraping** | **Enabled** |

**Results**:
- **Factual Correctness**: 0.38 (8 samples)
- **Abstract Quality**: 0.77 (6 samples)
- **Scraped**: 207 items (200 HTML, 7 PDF)
- **Chunks**: 3473
- **PDFs found**: 24 URLs discovered, 7 processed

**Notes**:
- **Regression detected**: Performance dropped compared to Exp 2 (Factual 0.75 -> 0.38).
- Larger dataset (3473 chunks vs 1603) likely diluted retrieval quality.
- PDF content might be introducing noise or formatting issues.
- `max_depth` of 3 reached 200 pages quickly.

---

### Exp 2 — Extended Coverage (2026-01-20)  
| Parameter | Value |
|-----------|-------|
| max_pages | 100 |
| max_depth | 5 |
| chunk_size | 1000 |
| chunk_overlap | 200 |

**Results**:
| Metric | Score | Samples |
|--------|-------|---------|
| Factual Correctness | 0.75 | 8 |
| Abstract Quality | 0.90 | 6 |

**Notes**: 
- Scraped 100 pages (~1.25 MB), 1603 chunks created
- Site structure is flat — max depth reached was 2 despite setting 5
- Doubled page coverage improved corpus breadth

**LangSmith**: [Factual](https://smith.langchain.com/o/05bea788-b744-53cc-a55e-8f72f5bd94bb/datasets/4274bae4-4b4e-47b8-beff-875df22f77f0/compare?selectedSessions=37edcb97-0381-4bef-bf57-5ccd1cba02bd) | [Abstract](https://smith.langchain.com/o/05bea788-b744-53cc-a55e-8f72f5bd94bb/datasets/8b3f3d64-f35f-4cc1-b2ac-4977c00eb9b1/compare?selectedSessions=8ace77c1-9d4f-45ab-9903-b370a3ed74b6)

<details>
<summary>Learnings & Next Steps</summary>

*Learnings:*
- Site structure is shallow; `max_depth` has diminishing returns beyond 2-3
- Increasing `max_pages` directly improves corpus coverage
- Baseline chunking (1000/200) performs reasonably well

*Next:*
- Try smaller (500/50) and larger (2000/400) chunks
- Experiment with k value (top-k documents retrieved)
- Refine system prompt for better answer synthesis

</details>

---

### Exp 1 — Baseline (2026-01-16)
| Parameter | Value |
|-----------|-------|
| max_pages | 50 |
| max_depth | 2 |
| chunk_size | 1000 |
| chunk_overlap | 200 |

**Results**: Not formally evaluated (pre-framework setup)

**Notes**: Initial scraping used as baseline reference.


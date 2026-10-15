# CuraLLM

**An evidence-grounded, uncertainty-aware medical information assistant, built as a research and engineering project.**

> **Not medical advice.** CuraLLM is a portfolio/research project. It does not diagnose, and it does not recommend individual treatment. It is not for clinical use.

## Status

This project is at an early stage. Everything not marked "Done" below has **not been built or measured yet**.

| Component | Status |
|---|---|
| Repository setup (license, references, README) | Done |
| Data curation pipeline | Not started |
| QLoRA SFT and DPO on Llama-3.1-8B-Instruct | Not started |
| Hallucination taxonomy and hand-labelled evaluation set | Not started |
| Retrieval (RAG) over a public health corpus | Not started |
| Claim-level verification and abstention | Not started |
| Application and UI | Not started |

## Research question

> Does preference optimization (DPO) actually reduce medical hallucination, or does it mainly improve how much people prefer the answers?

A mixed or negative result is an acceptable outcome and will be reported as found.

## What the finished system is meant to do

```
User question
   -> safety / intent check (emergencies, diagnosis requests)
   -> fine-tuned model drafts an answer
   -> claims are extracted from the draft
   -> evidence is retrieved for each claim
   -> each claim is checked: SUPPORTED / UNCERTAIN / CONTRADICTED
   -> the system answers, hedges, or abstains
   -> answer shown with sources and an evidence trail
```

## Planned experiments

Conditions compared on the same held-out, hand-labelled questions: Base, SFT, SFT + DPO, then the same models with retrieval, then retrieval plus verification and abstention.

## Results

| Condition | Hallucination rate | Evidence coverage | Citation accuracy |
|---|---|---|---|
| Base | NOT YET MEASURED | NOT YET MEASURED | NOT YET MEASURED |
| SFT | NOT YET MEASURED | NOT YET MEASURED | NOT YET MEASURED |
| SFT + DPO | NOT YET MEASURED | NOT YET MEASURED | NOT YET MEASURED |
| + RAG | NOT YET MEASURED | NOT YET MEASURED | NOT YET MEASURED |
| + Verification / abstention | NOT YET MEASURED | NOT YET MEASURED | NOT YET MEASURED |

## Repository layout

Files marked **(exists)** are in the repo today. The rest are planned and will be created as each stage is built.

```
CuraLLM/
├── README.md                       (exists) this file: status, goals, layout
├── LICENSE                         (exists) MIT, covers the code only
├── .gitignore                      keeps data, model weights, checkpoints and secrets out of git
├── doc/
│   ├── References.md               (exists) papers the design is based on
│   ├── architecture.md             how the pieces fit together, and why
│   ├── evaluation.md               metrics, annotation guideline, statistics used
│   ├── dataset_card.md             data sources, licenses, filtering counts
│   ├── model_card.md               what the model is, what it is not, known limits
│   └── safety.md                   safety design and red-team results
├── notebooks/                      runnable Colab experiments, one per stage
│   └── (planned)                   data audit, SFT, DPO, evaluation, RAG, verification
├── configs/                        experiment settings (model, LoRA rank, learning rate, seed)
├── src/
│   ├── data/                       loading, cleaning, deduplication, leakage checks
│   ├── training/                   SFT and DPO with checkpoint/resume
│   ├── retrieval/                  chunking, embeddings, index, source metadata
│   ├── verification/               claim extraction and claim-vs-evidence checking
│   ├── safety/                     emergency/diagnosis routing and the abstention gate
│   ├── evaluation/                 metrics, judge-vs-human comparison, paired statistics
│   └── serving/                    API and user interface
└── tests/                          automated checks for the parts that can silently break
```

## Compute and environment (measured)

Hardware checked so far is a free Google Colab session: Tesla T4 (15.6 GB), compute capability 7.5, about 12 GiB system RAM. This GPU has no native bf16 support, so training uses fp16 compute. Whether 8B QLoRA SFT and DPO fit on this hardware is **not yet measured**.

## Limitations

- Statistical power will be limited by the size of a hand-labelled evaluation set.
- Retrieved evidence is only as trustworthy as its source.

## License

Code is MIT-licensed. The Llama-3.1 model weights and every dataset have their own licenses, which must be checked before use or redistribution.
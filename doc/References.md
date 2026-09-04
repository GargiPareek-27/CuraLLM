# References

Papers informing the design of CuraLLM. Organized by
pipeline stage.

## Base architecture & fine-tuning method
- Hu et al. (2021), LoRA: Low-Rank Adaptation of Large Language Models
  https://arxiv.org/abs/2106.09685
- Dettmers et al. (2023), QLoRA: Efficient Finetuning of Quantized LLMs
  https://arxiv.org/abs/2305.14314
- Rafailov et al. (2023), Direct Preference Optimization
  https://arxiv.org/abs/2305.18290

## Comparable / prior medical LLMs
- Toma et al. (2023), Clinical Camel
  https://arxiv.org/abs/2305.12031
- Han et al. (2023), MedAlpaca
  https://arxiv.org/abs/2304.08247
- Gururajan et al. (2024), Aloe: Fine-tuned Open Healthcare LLMs
  https://arxiv.org/abs/2405.01886
- Singhal et al. (2023), Med-PaLM (Large Language Models Encode Clinical Knowledge)
  https://arxiv.org/abs/2212.13138

## Evaluation
- Lin (2004), ROUGE
  https://aclanthology.org/W04-1013/
- Zhang et al. (2019), BERTScore
  https://arxiv.org/abs/1904.09675
- Zheng et al. (2023), Judging LLM-as-a-Judge (MT-Bench)
  https://arxiv.org/abs/2306.05685

## Safety / hallucination
- Medical Hallucinations in Foundation Models (2025)
  https://arxiv.org/abs/2503.05777

## Serving infrastructure
- Sheng et al. (2023), S-LoRA: Serving Thousands of Concurrent LoRA Adapters
  https://arxiv.org/abs/2311.03285

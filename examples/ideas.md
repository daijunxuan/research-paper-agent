# Papertrail research brief

**Proposed Untested Experiment Ideas:**

1. **Varying Adaptation Rank (Rank 4 vs. Rank 8 vs. Rank 16)**  
   *Motivation:* To investigate how different ranks affect adaptation quality and memory usage.  
   *Citation:* [E1]  
   *Hypothesis:* Increasing the adaptation rank will improve adaptation quality by allowing more trainable parameters, but may increase memory consumption.  
   *Baseline/Control:* Full fine-tuning under identical data splits and training budgets.  
   *One-Variable Ablation:* Compare adaptation quality across rank levels (4, 8, 16) while keeping other factors constant.  
   *Metrics:* Adaptation accuracy, memory usage, and inference latency.  
   *Failure Criterion:* If adaptation accuracy drops below 90% or memory usage exceeds 50% of available resources.  

2. **Model Layer Selection for Low-Rank Update**  
   *Motivation:* To determine which model layers benefit most from low-rank updates.  
   *Citation:* [E2]  
   *Hypothesis:* Certain layers (e.g., attention heads or residual connections) will show greater improvement when updated with low-rank matrices.  
   *Baseline/Control:* Full fine-tuning with identical preprocessing and random seeds.  
   *One-Variable Ablation:* Train models with and without low-rank updates on specific layers (e.g., top 10% of layers).  
   *Metrics:* Task performance (held-out task quality), adaptation accuracy, and computational efficiency.  
   *Failure Criterion:* If task performance decreases by more than 10% or computational cost increases by 20%.  

These experiments aim to explore adaptation strategies without relying on published benchmarks, using the provided sources.


## Evidence ledger

### [E1] Demo note · Low-rank adaptation — page 2 (demo)

Limitations and experiment planning. A small rank may restrict the adaptation space; a larger rank increases trainable parameters and memory. To isolate the effect of rank, compare rank 4, 8 and 16 while holding the adapted layers, training examples, optimizer and evaluation procedure fixed. Evaluate held-out task quality and peak memory. The hypothesis is that some tasks need greater adaptation capacity; this is a proposed hypothesis, not an observed result. A separate ablation should compare which layers receive the low-rank update. Do not change rank and layer selection in the same causal comparison. Training efficiency does not by itself establish inference latency improvements.

### [E2] Demo note · Low-rank adaptation — page 1 (demo)

SYNTHETIC TEACHING NOTE, NOT A PUBLISHED PAPER. Research question: can adaptation avoid updating every pretrained weight? Method: keep pretrained weights frozen and train a pair of low-rank matrices whose product defines an additive update. The trainable parameter budget depends on the rank and on the dimensions of the chosen layers. This note proposes measuring adaptation quality together with optimizer-state memory. It contains no measured benchmark results. The baseline is full fine-tuning under the same data split and training token budget. The proposed evaluation uses a held-out task set, identical preprocessing and multiple random seeds.


## Provenance

{
  "usage": {
    "provider": "local",
    "model": "Qwen/Qwen3-1.7B",
    "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "cold_start": false,
    "seconds": 70.597,
    "output_tokens": 372,
    "token_limit_reached": false,
    "quantization": "dynamic-int8",
    "dtype": "float32",
    "seed": 42,
    "thinking": false,
    "attempts": 2,
    "total_generation_seconds": 136.82
  },
  "validation": {
    "valid_reference_ids": true,
    "cited": [
      "E1",
      "E2"
    ],
    "available": 2,
    "semantic_support_verified": false,
    "note": "Citation IDs point to retrieved excerpts. Read the evidence to verify each claim."
  },
  "prompt_version": "1.7"
}
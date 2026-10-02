# Papertrail research brief

**Research Question**  
Can adaptation avoid updating every pretrained weight?  

**Method**  
The method involves keeping pretrained weights frozen and training a low-rank matrix whose product defines an additive update. The trainable parameter budget depends on the rank and dimensions of the chosen layers. The proposal measures adaptation quality alongside optimizer-state memory, using a held-out task set with identical preprocessing and random seeds.  

**Evidence**  
The evidence comes from the provided demo notes, specifically [E1] and [E2]. [E1] outlines a demonstration where pretrained weights are kept frozen, and a low-rank matrix is trained to define an additive update. The baseline compares full fine-tuning with the same data split and token budget. [E2] discusses limitations, including the impact of rank on adaptation space and the separation of hypotheses versus observed results. The evaluation isolates the effect of rank by comparing rank 4, 8, and 16, holding other factors constant.  

**Limitations**  
Limitations include the fact that the study is a demo note without measured benchmarks. The hypothesis is proposed but not empirically validated. The experimental setup lacks a direct comparison between different ranks, and the conclusion is based on theoretical reasoning rather than empirical results. Additionally, the held-out task set may not fully represent real-world scenarios, and the lack of training efficiency metrics limits generalizability.


## Evidence ledger

### [E1] Demo note · Low-rank adaptation — page 1 (demo)

SYNTHETIC TEACHING NOTE, NOT A PUBLISHED PAPER. Research question: can adaptation avoid updating every pretrained weight? Method: keep pretrained weights frozen and train a pair of low-rank matrices whose product defines an additive update. The trainable parameter budget depends on the rank and on the dimensions of the chosen layers. This note proposes measuring adaptation quality together with optimizer-state memory. It contains no measured benchmark results. The baseline is full fine-tuning under the same data split and training token budget. The proposed evaluation uses a held-out task set, identical preprocessing and multiple random seeds.

### [E2] Demo note · Low-rank adaptation — page 2 (demo)

Limitations and experiment planning. A small rank may restrict the adaptation space; a larger rank increases trainable parameters and memory. To isolate the effect of rank, compare rank 4, 8 and 16 while holding the adapted layers, training examples, optimizer and evaluation procedure fixed. Evaluate held-out task quality and peak memory. The hypothesis is that some tasks need greater adaptation capacity; this is a proposed hypothesis, not an observed result. A separate ablation should compare which layers receive the low-rank update. Do not change rank and layer selection in the same causal comparison. Training efficiency does not by itself establish inference latency improvements.


## Provenance

{
  "usage": {
    "provider": "local",
    "model": "Qwen/Qwen3-1.7B",
    "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "cold_start": false,
    "seconds": 55.43,
    "output_tokens": 280,
    "token_limit_reached": false,
    "quantization": "dynamic-int8",
    "dtype": "float32",
    "seed": 42,
    "thinking": false,
    "attempts": 2,
    "total_generation_seconds": 125.94300000000001
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
  "prompt_version": "1.6"
}
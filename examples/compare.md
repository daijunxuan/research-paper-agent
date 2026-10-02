# Papertrail research brief

The selected papers focus on different aspects of adaptation in language models. 

**Demo note · Low-rank adaptation** addresses how adapting a model can be done without updating all pretrained weights. It suggests keeping pretrained weights frozen and training only a few low-rank matrices, which can define an additive update. This approach allows for efficient adaptation with a manageable trainable parameter budget. The method emphasizes evaluating adaptation quality alongside optimizer state memory, highlighting the trade-off between computational efficiency and model performance. This paper supports the idea that low-rank adaptations can be effective without significant model retraining [E2].

**Demo note · Retrieval-Augmented Adaptation** explores whether external passage data can supply knowledge without updating model weights. It describes a method where documents are split into passages, indexed, and used to generate responses. The system retains the language model fixed while evaluating retrieval accuracy separately from answer quality. This paper highlights the potential of retrieval-based approaches to enhance model performance without modifying pre-trained weights [E3].

Both papers address adaptation strategies but differ in their methodologies. Low-rank adaptation focuses on reducing trainable parameters through matrix training, while retrieval augmentation leverages external data for improved response quality. The first paper emphasizes training efficiency, whereas the second highlights retrieval accuracy. Neither paper claims direct performance comparisons across datasets, focusing instead on theoretical frameworks and practical implications. These studies collectively illustrate the diverse approaches to model adaptation, each with its own strengths and limitations.


## Evidence ledger

### [E1] Demo note · Low-rank adaptation — page 2 (demo)

Limitations and experiment planning. A small rank may restrict the adaptation space; a larger rank increases trainable parameters and memory. To isolate the effect of rank, compare rank 4, 8 and 16 while holding the adapted layers, training examples, optimizer and evaluation procedure fixed. Evaluate held-out task quality and peak memory. The hypothesis is that some tasks need greater adaptation capacity; this is a proposed hypothesis, not an observed result. A separate ablation should compare which layers receive the low-rank update. Do not change rank and layer selection in the same causal comparison. Training efficiency does not by itself establish inference latency improvements.

### [E2] Demo note · Low-rank adaptation — page 1 (demo)

SYNTHETIC TEACHING NOTE, NOT A PUBLISHED PAPER. Research question: can adaptation avoid updating every pretrained weight? Method: keep pretrained weights frozen and train a pair of low-rank matrices whose product defines an additive update. The trainable parameter budget depends on the rank and on the dimensions of the chosen layers. This note proposes measuring adaptation quality together with optimizer-state memory. It contains no measured benchmark results. The baseline is full fine-tuning under the same data split and training token budget. The proposed evaluation uses a held-out task set, identical preprocessing and multiple random seeds.

### [E3] Demo note · Retrieval-augmented adaptation — page 1 (demo)

SYNTHETIC TEACHING NOTE, NOT A PUBLISHED PAPER. Research question: can external passages supply changing knowledge without updating model weights? Method: split documents into passages, index them, retrieve a small evidence set for each question and condition generation on those passages. A lexical retrieval baseline uses BM25. All cited passages retain document identifiers and page numbers. The proposed system keeps the language model fixed and evaluates retrieval separately from answer quality. Evaluation should measure evidence recall, unsupported claims and end-to-end latency. This note supplies no measured scores and does not claim that retrieval guarantees correct answers.

### [E4] Demo note · Retrieval-augmented adaptation — page 2 (demo)

Limitations and experiment planning. Retrieval failures can deprive generation of the necessary evidence. A useful ablation changes chunk size while keeping the corpus, overlap policy, query set and generator fixed. Another experiment compares top-k values of 2, 4 and 8 at a fixed context budget. Irrelevant retrieved passages may distract the generator, so increasing k is not assumed to improve answer quality. Citation IDs can be validated mechanically, but an existing citation does not prove that its passage entails the generated claim. An unanswerable-query set should measure when the system correctly abstains rather than inventing an answer.


## Provenance

{
  "usage": {
    "provider": "local",
    "model": "Qwen/Qwen3-1.7B",
    "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "cold_start": false,
    "seconds": 60.983,
    "output_tokens": 286,
    "token_limit_reached": false,
    "quantization": "dynamic-int8",
    "dtype": "float32",
    "seed": 42,
    "thinking": false,
    "attempts": 1,
    "total_generation_seconds": 60.983
  },
  "validation": {
    "valid_reference_ids": true,
    "cited": [
      "E2",
      "E3"
    ],
    "available": 4,
    "semantic_support_verified": false,
    "note": "Citation IDs point to retrieved excerpts. Read the evidence to verify each claim."
  },
  "prompt_version": "1.6"
}
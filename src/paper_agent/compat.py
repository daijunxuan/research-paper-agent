"""Narrow compatibility for the pinned Torch/Transformers pair on macOS 13.

Torch 2.6's MPS integer isin kernel requires macOS 14. Transformers 4.51.3
selects that kernel based only on Torch's version. Use broadcast equality for
its token-membership helper during generation; restore the helpers afterwards.
The app runs one model worker, so generation calls cannot overlap this scope.
"""

from contextlib import contextmanager


def broadcast_isin(elements, test_elements):
    import torch

    candidates = torch.as_tensor(test_elements, device=elements.device).reshape(-1)
    return (elements.unsqueeze(-1) == candidates).any(dim=-1)


@contextmanager
def legacy_mps_membership(device):
    import torch

    if device != "mps" or torch.backends.mps.is_macos_or_newer(14, 0):
        yield
        return
    from transformers.generation import logits_process, stopping_criteria, utils

    modules = (utils, stopping_criteria, logits_process)
    originals = [module.isin_mps_friendly for module in modules]
    try:
        for module in modules:
            module.isin_mps_friendly = broadcast_isin
        yield
    finally:
        for module, original in zip(modules, originals):
            module.isin_mps_friendly = original

import pytest


def test_token_membership_preserves_scalar_vector_and_matrix_shapes():
    torch = pytest.importorskip("torch")
    from paper_agent.compat import broadcast_isin

    for values in [1, [1, 3, 5], [[1, 2], [3, 4]]]:
        elements = torch.tensor(values)
        for candidates in [torch.tensor([1, 4]), torch.tensor(3), torch.tensor([])]:
            actual = broadcast_isin(elements, candidates)
            assert torch.equal(actual, torch.isin(elements, candidates))
            assert actual.shape == elements.shape

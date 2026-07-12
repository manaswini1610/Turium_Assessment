import math

from app.services.retrieval_service import cosine_similarity


def test_cosine_similarity_identical_vectors_is_one():
    a = [1.0, 0.0, 0.0]
    assert math.isclose(cosine_similarity(a, a), 1.0, rel_tol=1e-6)


def test_cosine_similarity_orthogonal_vectors_is_zero():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert math.isclose(cosine_similarity(a, b), 0.0, abs_tol=1e-9)


def test_cosine_similarity_opposite_vectors_is_negative_one():
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    assert math.isclose(cosine_similarity(a, b), -1.0, rel_tol=1e-6)


def test_cosine_similarity_zero_vector_returns_zero():
    a = [0.0, 0.0]
    b = [1.0, 1.0]
    assert cosine_similarity(a, b) == 0.0


def test_cosine_similarity_scale_invariant():
    a = [1.0, 2.0, 3.0]
    b = [2.0, 4.0, 6.0]
    assert math.isclose(cosine_similarity(a, b), 1.0, rel_tol=1e-6)

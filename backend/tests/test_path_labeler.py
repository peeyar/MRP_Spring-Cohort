"""Tests for path_labeler.py"""

import pytest
from path_labeler import label_path


@pytest.mark.parametrize("score,expected", [
    (100, "Warm Path"),
    (70, "Warm Path"),
    (69, "Stretch Path"),
    (40, "Stretch Path"),
    (39, "Explore"),
    (1, "Explore"),
    (0, "Explore"),
])
def test_label_path_thresholds(score, expected):
    assert label_path(score) == expected

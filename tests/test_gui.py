import pytest

from pricetyper.ui.gui import _is_unverified_send_error


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (None, False),
        ("", False),
        ("send_unverified: Enter was dispatched", True),
        ("browser action failed", False),
    ],
)
def test_unverified_send_error_check_accepts_optional_error(error, expected):
    assert _is_unverified_send_error(error) is expected

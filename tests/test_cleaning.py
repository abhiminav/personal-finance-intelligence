import pytest

from categorization.cleaning import clean_description


@pytest.mark.parametrize(
    "raw_description, expected",
    [
        (
            "PHONEPE*SWIGGYBLR",
            "swiggy",
        ),
        (
            "UPI/423819271/SWIGGY/paytm",
            "swiggy",
        ),
        (
            "SWIGGY*ORDER668497",
            "swiggy",
        ),
        (
            "POS 4990 SWIGGY",
            "swiggy",
        ),
        (
            "UPI/304514/SWIGGY/okaxis",
            "swiggy",
        ),
    ],
)
def test_clean_swiggy_variants(
    raw_description,
    expected,
):
    assert clean_description(raw_description) == expected


def test_clean_description_is_case_insensitive():
    assert (
        clean_description("phonepe*swiggyblr")
        == "swiggy"
    )


def test_clean_description_strips_whitespace():
    assert (
        clean_description("   SWIGGY   ")
        == "swiggy"
    )


def test_clean_description_rejects_non_string():
    with pytest.raises(TypeError):
        clean_description(None)


def test_clean_description_removes_reference_number():
    result = clean_description(
        "UPI/123456789/SWIGGY/paytm"
    )

    assert result == "swiggy"


def test_clean_description_removes_order_number():
    result = clean_description(
        "SWIGGY*ORDER987654"
    )

    assert result == "swiggy"
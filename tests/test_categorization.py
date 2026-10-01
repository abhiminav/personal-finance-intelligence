from categorization.merchant_dictionary import (
    get_merchant_by_id,
    resolve_exact_merchant,
)

from categorization.rule_based import classify_transaction

from categorization.counterparty import (
    extract_counterparty,
)

import pytest

from categorization.ml_classifier import MLClassifier


def test_resolve_swiggy():
    merchant = resolve_exact_merchant("swiggy")

    assert merchant is not None
    assert merchant.merchant_id == "swiggy"
    assert merchant.name == "Swiggy"
    assert merchant.category == "food & dining"


def test_resolve_amazon():
    merchant = resolve_exact_merchant("amazon")

    assert merchant is not None
    assert merchant.merchant_id == "amazon"
    assert merchant.name == "Amazon"
    assert merchant.category == "shopping"


def test_resolve_unknown_merchant():
    merchant = resolve_exact_merchant(
        "completely_unknown_merchant"
    )

    assert merchant is None


def test_get_merchant_by_id():
    merchant = get_merchant_by_id("uber")

    assert merchant is not None
    assert merchant.name == "Uber"
    assert merchant.category == "transport"


def test_get_unknown_merchant():
    merchant = get_merchant_by_id(
        "does_not_exist"
    )

    assert merchant is None


def test_classify_swiggy_variant():
    result = classify_transaction(
        "PHONEPE*SWIGGYBLR"
    )

    assert result.merchant_id == "swiggy"
    assert result.merchant_name == "Swiggy"
    assert result.category == "food & dining"
    assert result.method == "exact"
    assert result.confidence == 100.0


def test_classify_amazon_variant():
    result = classify_transaction(
        "POS 4521 AMAZON"
    )

    assert result.merchant_id == "amazon"
    assert result.merchant_name == "Amazon"
    assert result.category == "shopping"
    assert result.method == "exact"
    assert result.confidence == 100.0


def test_classify_uber_variant():
    result = classify_transaction(
        "UPI/123456/UBER/okaxis"
    )

    assert result.merchant_id == "uber"
    assert result.merchant_name == "Uber"
    assert result.category == "transport"
    assert result.method == "exact"
    assert result.confidence == 100.0


def test_classify_unknown_transaction():
    result = classify_transaction(
        "SOME_UNKNOWN_MERCHANT_123"
    )

    assert result.merchant_id is None
    assert result.merchant_name is None
    assert result.category is None
    assert result.method == "unresolved"
    assert result.confidence < 80


def test_fuzzy_match_swiggy():
    result = classify_transaction(
        "SWIGGY INDIA"
    )

    assert result.merchant_id == "swiggy"
    assert result.merchant_name == "Swiggy"
    assert result.category == "food & dining"
    assert result.method == "fuzzy"
    assert result.confidence >= 80


def test_fuzzy_match_amazon_typo():
    result = classify_transaction(
        "AMAZN"
    )

    assert result.merchant_id == "amazon"
    assert result.merchant_name == "Amazon"
    assert result.category == "shopping"
    assert result.method == "fuzzy"
    assert result.confidence >= 80


def test_fuzzy_match_flipkart():
    result = classify_transaction(
        "FLIPKART ONLINE"
    )

    assert result.merchant_id == "flipkart"
    assert result.merchant_name == "Flipkart"
    assert result.category == "shopping"
    assert result.method == "fuzzy"
    assert result.confidence >= 80


def test_fuzzy_match_uber():
    result = classify_transaction(
        "UBER INDIA"
    )

    assert result.merchant_id == "uber"
    assert result.merchant_name == "Uber"
    assert result.category == "transport"
    assert result.method == "fuzzy"
    assert result.confidence >= 80


def test_low_confidence_match_returns_none():
    result = classify_transaction(
        "COMPLETELY_UNRELATED_TRANSACTION"
    )

    assert result.merchant_id is None
    assert result.merchant_name is None
    assert result.category is None
    assert result.method == "unresolved"
    assert result.confidence < 80


def test_extract_counterparty_upi():
    counterparty = extract_counterparty(
        "UPI/709931/RAJESH KUMAR/paytm"
    )

    assert counterparty is not None
    assert counterparty.counterparty_id == "rajesh_kumar"
    assert counterparty.name == "Rajesh Kumar"
    assert counterparty.category == "transfers/P2P"


def test_extract_counterparty_upi_hyphen():
    counterparty = extract_counterparty(
        "UPI-369993-AMIT VERMA"
    )

    assert counterparty is not None
    assert counterparty.counterparty_id == "amit_verma"
    assert counterparty.name == "Amit Verma"


def test_extract_counterparty_imps():
    counterparty = extract_counterparty(
        "IMPS/P2A/651206/Amit Verma"
    )

    assert counterparty is not None
    assert counterparty.counterparty_id == "amit_verma"
    assert counterparty.name == "Amit Verma"


def test_extract_counterparty_rohit():
    counterparty = extract_counterparty(
        "UPI/257177/ROHIT S/paytm"
    )

    assert counterparty is not None
    assert counterparty.counterparty_id == "rohit_s"
    assert counterparty.name == "Rohit S"


def test_extract_counterparty_unknown():
    counterparty = extract_counterparty(
        "UPI/123456/UNKNOWN PERSON/paytm"
    )

    assert counterparty is None


def test_extract_counterparty_non_string():
    with pytest.raises(TypeError):
        extract_counterparty(None)


def test_classify_counterparty_rajash_kumar():
    result = classify_transaction(
        "UPI/709931/RAJESH KUMAR/paytm"
    )

    assert result.merchant_id is None
    assert result.merchant_name is None
    assert result.counterparty_id == "rajesh_kumar"
    assert result.counterparty_name == "Rajesh Kumar"
    assert result.category == "transfers/P2P"
    assert result.method == "counterparty"
    assert result.confidence == 100.0


def test_classify_counterparty_imps():
    result = classify_transaction(
        "IMPS/P2A/651206/Amit Verma"
    )

    assert result.merchant_id is None
    assert result.merchant_name is None
    assert result.counterparty_id == "amit_verma"
    assert result.counterparty_name == "Amit Verma"
    assert result.category == "transfers/P2P"
    assert result.method == "counterparty"


def test_merchant_match_takes_priority_over_counterparty():
    result = classify_transaction(
        "PHONEPE*SWIGGYBLR"
    )

    assert result.merchant_id == "swiggy"
    assert result.merchant_name == "Swiggy"
    assert result.counterparty_id is None
    assert result.counterparty_name is None
    assert result.category == "food & dining"


def test_ml_classifier_can_train_and_predict():
    classifier = MLClassifier()

    descriptions = [
        "SWIGGY",
        "ZOMATO",
        "AMAZON",
        "FLIPKART",
        "UBER",
        "OLA",
    ]

    categories = [
        "food & dining",
        "food & dining",
        "shopping",
        "shopping",
        "transport",
        "transport",
    ]

    classifier.fit(
        descriptions,
        categories,
    )

    predictions = classifier.predict(
        ["SWIGGY", "AMAZON", "UBER"]
    )

    assert len(predictions) == 3
    assert predictions[0] == "food & dining"
    assert predictions[1] == "shopping"
    assert predictions[2] == "transport"


def test_ml_classifier_requires_training():
    classifier = MLClassifier()

    try:
        classifier.predict(["SWIGGY"])
        assert False
    except RuntimeError as error:
        assert "fitted" in str(error)


def test_ml_classifier_probability_output():
    classifier = MLClassifier()

    descriptions = [
        "SWIGGY",
        "ZOMATO",
        "AMAZON",
        "FLIPKART",
    ]

    categories = [
        "food & dining",
        "food & dining",
        "shopping",
        "shopping",
    ]

    classifier.fit(
        descriptions,
        categories,
    )

    probabilities = classifier.predict_proba(
        ["SWIGGY"]
    )

    assert probabilities.shape[0] == 1
    assert probabilities.shape[1] == 2


def test_ml_classifier_prediction_with_confidence():
    classifier = MLClassifier()

    descriptions = [
        "SWIGGY",
        "AMAZON",
        "UBER",
        "NETFLIX",
    ]

    categories = [
        "food & dining",
        "shopping",
        "transport",
        "subscriptions",
    ]

    classifier.fit(
        descriptions,
        categories,
    )

    results = classifier.predict_with_confidence(
        ["SWIGGY", "AMAZON"]
    )

    assert len(results) == 2

    for prediction, confidence in results:
        assert isinstance(prediction, str)
        assert 0.0 <= confidence <= 1.0


def test_ml_train_test_split_is_stratified():
    from evaluation.ml_dataset import (
        get_ml_train_test_split,
    )

    (
        X_train,
        X_test,
        y_train,
        y_test,
    ) = get_ml_train_test_split()

    assert len(X_train) == 1914
    assert len(X_test) == 479

    assert len(y_train) == 1914
    assert len(y_test) == 479

    assert set(y_train) == set(y_test)


def test_hybrid_classifier_uses_rule_based_match_before_ml():
    from categorization.ml_classifier import MLClassifier
    from categorization.rule_based import classify_transaction

    classifier = MLClassifier()

    descriptions = [
        "SWIGGY INDIA ONLINE",
        "AMAZON PAY IN",
        "UBER INDIA TRIP",
        "POWER BILL",
        "HOUSE RENT PAYMENT",
    ]

    categories = [
        "food & dining",
        "shopping",
        "transport",
        "utilities",
        "rent",
    ]

    classifier.fit(
        descriptions,
        categories,
    )

    result = classify_transaction(
        "SWIGGY INDIA ONLINE",
        ml_classifier=classifier,
    )

    assert result.method == "fuzzy"
    assert result.category == "food & dining"


def test_hybrid_classifier_returns_ml_result_for_unknown_merchant():
    from categorization.ml_classifier import MLClassifier
    from categorization.rule_based import classify_transaction

    classifier = MLClassifier()

    descriptions = [
        "MEALBOX FOOD DELIVERY",
        "MEALBOX FOOD ORDER",
        "MEALBOX RESTAURANT ORDER",
        "SHOPMART ONLINE STORE",
        "SHOPMART PRODUCT ORDER",
        "SHOPMART RETAIL PURCHASE",
        "CABRIDE TAXI SERVICE",
        "CABRIDE TAXI TRIP",
        "CABRIDE CAR SERVICE",
    ]

    categories = [
        "food & dining",
        "food & dining",
        "food & dining",
        "shopping",
        "shopping",
        "shopping",
        "transport",
        "transport",
        "transport",
    ]

    classifier.fit(
        descriptions,
        categories,
    )

    result = classify_transaction(
        "MEALBOX FOOD PURCHASE",
        ml_classifier=classifier,
    )

    assert result.method == "ml"
    assert result.category == "food & dining"
    assert result.confidence >= 40.0


def test_hybrid_classifier_keeps_counterparty_separate():
    from categorization.ml_classifier import MLClassifier
    from categorization.rule_based import classify_transaction

    classifier = MLClassifier()

    descriptions = [
        "SWIGGY INDIA ONLINE",
        "AMAZON PAY IN",
        "UBER INDIA TRIP",
        "POWER BILL",
        "HOUSE RENT PAYMENT",
        "RAJESH KUMAR",
    ]

    categories = [
        "food & dining",
        "shopping",
        "transport",
        "utilities",
        "rent",
        "transfers/P2P",
    ]

    classifier.fit(
        descriptions,
        categories,
    )

    result = classify_transaction(
        "UPI/829193/RAJESH KUMAR/paytm",
        ml_classifier=classifier,
    )

    assert result.method == "counterparty"
    assert result.category == "transfers/P2P"
    assert result.counterparty_name == "Rajesh Kumar"
    assert result.merchant_name is None


def test_hybrid_classifier_can_return_unresolved():
    from categorization.ml_classifier import MLClassifier
    from categorization.rule_based import classify_transaction

    classifier = MLClassifier()

    descriptions = [
        "SWIGGY INDIA ONLINE",
        "AMAZON PAY IN",
        "UBER INDIA TRIP",
        "POWER BILL",
        "HOUSE RENT PAYMENT",
    ]

    categories = [
        "food & dining",
        "shopping",
        "transport",
        "utilities",
        "rent",
    ]

    classifier.fit(
        descriptions,
        categories,
    )

    result = classify_transaction(
        "COMPLETELY UNKNOWN TRANSACTION XYZ",
        ml_classifier=classifier,
    )

    assert result.method == "unresolved"
    assert result.category is None

def test_normalize_merchant_name():
    from categorization.merchant_clustering import (
        normalize_merchant_name,
    )

    assert (
        normalize_merchant_name(
            "PAYTM*SWIGGYBLR"
        )
        == "swiggy"
    )


def test_normalize_merchant_with_transaction_id():
    from categorization.merchant_clustering import (
        normalize_merchant_name,
    )

    assert (
        normalize_merchant_name(
            "UPI-SWIGGY-482193-okaxis"
        )
        == "swiggy"
    )


def test_normalize_merchant_removes_generic_words():
    from categorization.merchant_clustering import (
        normalize_merchant_name,
    )

    assert (
        normalize_merchant_name(
            "SWIGGY INDIA ONLINE ORDER"
        )
        == "swiggy"
    )


def test_merchant_similarity():
    from categorization.merchant_clustering import (
        merchant_similarity,
    )

    score = merchant_similarity(
        "PAYTM*SWIGGYBLR",
        "SWIGGY INDIA ONLINE",
    )

    assert score == 100.0


def test_merchant_similarity_different_merchants():
    from categorization.merchant_clustering import (
        merchant_similarity,
    )

    score = merchant_similarity(
        "SWIGGY",
        "AMAZON",
    )

    assert score < 80.0


def test_cluster_merchants_groups_swggy_variants():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    names = [
        "PAYTM*SWIGGYBLR",
        "SWIGGY INDIA ONLINE",
        "UPI-SWIGGY-482193-okaxis",
        "SWIGGY FOOD ORDER",
    ]

    clusters = cluster_merchants(names)

    assert len(clusters) == 1
    assert len(clusters[0].members) == 4


def test_cluster_merchants_keeps_different_merchants_separate():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    names = [
        "SWIGGY",
        "ZOMATO",
        "AMAZON",
        "FLIPKART",
    ]

    clusters = cluster_merchants(names)

    assert len(clusters) == 4


def test_cluster_merchants_groups_multiple_merchants():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    names = [
        "PAYTM*SWIGGYBLR",
        "SWIGGY INDIA ONLINE",
        "AMAZON INDIA",
        "AMAZON ONLINE STORE",
        "UBER DEL",
        "UBER INDIA TRIP",
    ]

    clusters = cluster_merchants(names)

    assert len(clusters) == 3

    cluster_sizes = sorted(
        len(cluster.members)
        for cluster in clusters
    )

    assert cluster_sizes == [2, 2, 2]


def test_cluster_merchants_empty_input():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    clusters = cluster_merchants([])

    assert clusters == []


def test_cluster_merchants_invalid_threshold():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    with pytest.raises(ValueError):
        cluster_merchants(
            ["SWIGGY"],
            threshold=101,
        )


def test_cluster_merchants_requires_list():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    with pytest.raises(TypeError):
        cluster_merchants("SWIGGY")


def test_cluster_resolves_to_canonical_swiggy():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    names = [
        "PAYTM*SWIGGYBLR",
        "SWIGGY INDIA ONLINE",
        "UPI-SWIGGY-482193-okaxis",
        "SWIGGY FOOD ORDER",
    ]

    clusters = cluster_merchants(names)

    assert len(clusters) == 1

    cluster = clusters[0]

    assert cluster.canonical_name == "Swiggy"
    assert cluster.merchant_id == "swiggy"
    assert cluster.category == "food & dining"
    assert len(cluster.members) == 4


def test_cluster_resolves_to_canonical_amazon():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    names = [
        "AMAZON INDIA",
        "AMAZON ONLINE STORE",
        "PAYMENT AMAZON",
    ]

    clusters = cluster_merchants(names)

    assert len(clusters) == 1

    cluster = clusters[0]

    assert cluster.canonical_name == "Amazon"
    assert cluster.merchant_id == "amazon"
    assert cluster.category == "shopping"


def test_cluster_resolves_multiple_canonical_merchants():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    names = [
        "PAYTM*SWIGGYBLR",
        "SWIGGY INDIA ONLINE",
        "AMAZON INDIA",
        "AMAZON ONLINE STORE",
        "UBER DEL",
        "UBER INDIA TRIP",
    ]

    clusters = cluster_merchants(names)

    assert len(clusters) == 3

    canonical_names = {
        cluster.canonical_name
        for cluster in clusters
    }

    assert canonical_names == {
        "Swiggy",
        "Amazon",
        "Uber",
    }


def test_unknown_cluster_has_no_canonical_merchant():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    clusters = cluster_merchants(
        ["COMPLETELY UNKNOWN BUSINESS XYZ"]
    )

    assert len(clusters) == 1

    cluster = clusters[0]

    assert cluster.merchant_id is None
    assert cluster.category is None


def test_counterparty_transactions_are_excluded_from_merchant_clustering():
    from categorization.merchant_clustering import (
        cluster_merchants,
    )

    names = [
        "PAYTM*SWIGGYBLR",
        "UPI/709931/RAJESH KUMAR/paytm",
        "IMPS/P2A/476339/Rajesh Kumar",
        "SWIGGY INDIA ONLINE",
    ]

    clusters = cluster_merchants(names)

    assert len(clusters) == 1

    cluster = clusters[0]

    assert cluster.canonical_name == "Swiggy"
    assert cluster.merchant_id == "swiggy"
    assert cluster.category == "food & dining"
    assert len(cluster.members) == 2

    assert all(
        "RAJESH KUMAR" not in member.upper()
        for member in cluster.members
    )


def test_set_and_get_category_override():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    store.set_override(
        "amazon",
        "food & dining",
    )

    assert store.get_override("amazon") == "food & dining"


def test_missing_override_returns_none():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    assert store.get_override("amazon") is None


def test_has_override():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    assert store.has_override("amazon") is False

    store.set_override(
        "amazon",
        "food & dining",
    )

    assert store.has_override("amazon") is True


def test_override_can_be_replaced():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    store.set_override(
        "amazon",
        "shopping",
    )

    store.set_override(
        "amazon",
        "food & dining",
    )

    assert store.get_override("amazon") == "food & dining"


def test_remove_override():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    store.set_override(
        "amazon",
        "shopping",
    )

    assert store.remove_override("amazon") is True
    assert store.get_override("amazon") is None


def test_remove_missing_override():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    assert store.remove_override("amazon") is False


def test_get_all_overrides():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    store.set_override(
        "amazon",
        "shopping",
    )

    store.set_override(
        "swiggy",
        "groceries",
    )

    overrides = store.get_all_overrides()

    assert len(overrides) == 2

    categories = {
        override.merchant_id: override.category
        for override in overrides
    }

    assert categories == {
        "amazon": "shopping",
        "swiggy": "groceries",
    }


def test_override_requires_string_merchant_id():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    try:
        store.set_override(
            123,
            "shopping",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Expected TypeError"
        )


def test_override_requires_non_empty_merchant_id():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    try:
        store.set_override(
            "   ",
            "shopping",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_override_requires_non_empty_category():
    from categorization.overrides import OverrideStore

    store = OverrideStore()

    try:
        store.set_override(
            "amazon",
            "   ",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_override_takes_priority_over_exact_merchant():
    from categorization.overrides import OverrideStore
    from categorization.rule_based import classify_transaction

    store = OverrideStore()

    store.set_override(
        "amazon",
        "food & dining",
    )

    result = classify_transaction(
        "AMAZON",
        override_store=store,
    )

    assert result.merchant_id == "amazon"
    assert result.merchant_name == "Amazon"
    assert result.category == "food & dining"
    assert result.method == "override"
    assert result.confidence == 100.0


def test_without_override_normal_category_is_used():
    from categorization.overrides import OverrideStore
    from categorization.rule_based import classify_transaction

    store = OverrideStore()

    result = classify_transaction(
        "AMAZON",
        override_store=store,
    )

    assert result.merchant_id == "amazon"
    assert result.category == "shopping"
    assert result.method == "exact"


def test_override_works_with_fuzzy_merchant_match():
    from categorization.overrides import OverrideStore
    from categorization.rule_based import classify_transaction

    store = OverrideStore()

    store.set_override(
        "swiggy",
        "groceries",
    )

    result = classify_transaction(
        "SWIGGY INDIA ONLINE",
        override_store=store,
    )

    assert result.merchant_id == "swiggy"
    assert result.merchant_name == "Swiggy"
    assert result.category == "groceries"
    assert result.method == "override"


def test_classifier_works_without_override_store():
    from categorization.rule_based import classify_transaction

    result = classify_transaction("AMAZON")

    assert result.merchant_id == "amazon"
    assert result.category == "shopping"
    assert result.method == "exact"
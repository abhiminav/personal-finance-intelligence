from rapidfuzz import fuzz, process

from categorization.cleaning import clean_description
from categorization.counterparty import extract_counterparty
from categorization.merchant_dictionary import (
    MERCHANT_LOOKUP,
    resolve_exact_merchant,
)
from categorization.ml_classifier import MLClassifier
from categorization.overrides import OverrideStore
from data.schemas import ClassificationResult


FUZZY_THRESHOLD = 80
ML_CONFIDENCE_THRESHOLD = 0.40


def classify_transaction(
    description: str,
    ml_classifier: MLClassifier | None = None,
    override_store: OverrideStore | None = None,
) -> ClassificationResult:
    """
    Classify a transaction using a hybrid rule-based + ML approach.

    Classification order:

        1. User override
        2. Exact merchant matching
        3. Fuzzy merchant matching
        4. Counterparty extraction
        5. ML classification
        6. Unresolved

    User-defined overrides always take priority over
    automatic classification.

    Deterministic merchant matches take priority
    over the ML classifier.

    ML predictions are accepted only when their confidence
    meets ML_CONFIDENCE_THRESHOLD.
    """

    cleaned = clean_description(description)

    # ---------------------------------------------------------
    # 1. User override
    # ---------------------------------------------------------

    if override_store is not None:
        merchant = resolve_exact_merchant(cleaned)

        if merchant is not None:
            override_category = override_store.get_override(
                merchant.merchant_id
            )

            if override_category is not None:
                return ClassificationResult(
                    merchant_id=merchant.merchant_id,
                    merchant_name=merchant.name,
                    counterparty_id=None,
                    counterparty_name=None,
                    category=override_category,
                    method="override",
                    confidence=100.0,
                )

    # ---------------------------------------------------------
    # 2. Exact merchant matching
    # ---------------------------------------------------------

    merchant = resolve_exact_merchant(cleaned)

    if merchant is not None:
        return ClassificationResult(
            merchant_id=merchant.merchant_id,
            merchant_name=merchant.name,
            counterparty_id=None,
            counterparty_name=None,
            category=merchant.category,
            method="exact",
            confidence=100.0,
        )

    # ---------------------------------------------------------
    # 3. Fuzzy merchant matching
    # ---------------------------------------------------------

    merchant_ids = list(MERCHANT_LOOKUP.keys())

    result = process.extractOne(
        cleaned,
        merchant_ids,
        scorer=fuzz.WRatio,
    )

    if result is not None:
        matched_merchant_id, score, _ = result

        if score >= FUZZY_THRESHOLD:
            merchant = MERCHANT_LOOKUP[matched_merchant_id]

            override_category = None

            if override_store is not None:
                override_category = (
                    override_store.get_override(
                        merchant.merchant_id
                    )
                )

            if override_category is not None:
                return ClassificationResult(
                    merchant_id=merchant.merchant_id,
                    merchant_name=merchant.name,
                    counterparty_id=None,
                    counterparty_name=None,
                    category=override_category,
                    method="override",
                    confidence=100.0,
                )

            return ClassificationResult(
                merchant_id=merchant.merchant_id,
                merchant_name=merchant.name,
                counterparty_id=None,
                counterparty_name=None,
                category=merchant.category,
                method="fuzzy",
                confidence=float(score),
            )

    # ---------------------------------------------------------
    # 4. Counterparty extraction
    # ---------------------------------------------------------

    counterparty = extract_counterparty(description)

    if counterparty is not None:
        return ClassificationResult(
            merchant_id=None,
            merchant_name=None,
            counterparty_id=counterparty.counterparty_id,
            counterparty_name=counterparty.name,
            category="transfers/P2P",
            method="counterparty",
            confidence=100.0,
        )

    # ---------------------------------------------------------
    # 5. ML fallback
    # ---------------------------------------------------------

    if ml_classifier is not None:
        prediction, confidence = (
            ml_classifier.predict_with_confidence(
                [cleaned]
            )[0]
        )

        if confidence >= ML_CONFIDENCE_THRESHOLD:
            return ClassificationResult(
                merchant_id=None,
                merchant_name=None,
                counterparty_id=None,
                counterparty_name=None,
                category=prediction,
                method="ml",
                confidence=confidence * 100,
            )

        return ClassificationResult(
            merchant_id=None,
            merchant_name=None,
            counterparty_id=None,
            counterparty_name=None,
            category=None,
            method="unresolved",
            confidence=confidence * 100,
        )

    # ---------------------------------------------------------
    # 6. Unresolved when ML is unavailable
    # ---------------------------------------------------------

    confidence = float(result[1]) if result is not None else 0.0

    return ClassificationResult(
        merchant_id=None,
        merchant_name=None,
        counterparty_id=None,
        counterparty_name=None,
        category=None,
        method="unresolved",
        confidence=confidence,
    )
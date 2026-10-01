from collections import Counter

from sklearn.metrics import accuracy_score

from categorization.ml_classifier import MLClassifier
from categorization.rule_based import classify_transaction
from data.synthetic_generator import generate_dataset
from evaluation.generalization_dataset import GENERALIZATION_EXAMPLES


def evaluate_rule_based(transactions):
    """Evaluate the deterministic rule-based classifier."""

    predictions = []
    actual = []
    methods = []

    for transaction in transactions:
        result = classify_transaction(
            transaction.raw_description
        )

        predictions.append(result.category)
        actual.append(transaction.category)
        methods.append(result.method)

    resolved_predictions = [
        prediction
        for prediction in predictions
        if prediction is not None
    ]

    resolved_actual = [
        actual_value
        for prediction, actual_value in zip(
            predictions,
            actual,
        )
        if prediction is not None
    ]

    return {
        "accuracy": accuracy_score(
            resolved_actual,
            resolved_predictions,
        ),
        "total": len(transactions),
        "resolved": len(resolved_predictions),
        "unresolved": predictions.count(None),
        "methods": Counter(methods),
    }


def train_ml_classifier(transactions):
    """Train the ML classifier on the synthetic dataset."""

    descriptions = [
        transaction.raw_description
        for transaction in transactions
    ]

    categories = [
        transaction.category
        for transaction in transactions
    ]

    classifier = MLClassifier()

    classifier.fit(
        descriptions,
        categories,
    )

    return classifier


def evaluate_ml(classifier):
    """Evaluate ML on the unseen generalization benchmark."""

    descriptions = [
        example.description
        for example in GENERALIZATION_EXAMPLES
    ]

    actual = [
        example.category
        for example in GENERALIZATION_EXAMPLES
    ]

    results = classifier.predict_with_confidence(
        descriptions
    )

    predictions = [
        prediction
        for prediction, _ in results
    ]

    return {
        "accuracy": accuracy_score(
            actual,
            predictions,
        ),
        "total": len(actual),
        "predictions": predictions,
        "actual": actual,
        "results": results,
    }


def evaluate_hybrid(classifier):
    """Evaluate the hybrid classifier on the unseen benchmark."""

    predictions = []
    actual = []
    methods = []
    confidences = []

    for example in GENERALIZATION_EXAMPLES:
        result = classify_transaction(
            example.description,
            ml_classifier=classifier,
        )

        predictions.append(result.category)
        actual.append(example.category)
        methods.append(result.method)
        confidences.append(result.confidence)

    resolved_predictions = [
        prediction
        for prediction in predictions
        if prediction is not None
    ]

    resolved_actual = [
        actual_value
        for prediction, actual_value in zip(
            predictions,
            actual,
        )
        if prediction is not None
    ]

    return {
        "accuracy": accuracy_score(
            resolved_actual,
            resolved_predictions,
        ),
        "total": len(actual),
        "resolved": len(resolved_predictions),
        "unresolved": predictions.count(None),
        "predictions": predictions,
        "actual": actual,
        "methods": methods,
        "method_counts": Counter(methods),
        "confidences": confidences,
    }


def print_summary(
    rule_based_result,
    ml_result,
    hybrid_result,
):
    """Print a compact comparison of all approaches."""

    print()
    print("=" * 70)
    print("CLASSIFICATION SYSTEM COMPARISON")
    print("=" * 70)

    print()
    print(
        f"{'System':<20}"
        f"{'Accuracy':>12}"
        f"{'Resolved':>12}"
        f"{'Unresolved':>14}"
    )

    print("-" * 70)

    print(
        f"{'Rule-based':<20}"
        f"{rule_based_result['accuracy'] * 100:>11.2f}%"
        f"{rule_based_result['resolved']:>12}"
        f"{rule_based_result['unresolved']:>14}"
    )

    print(
        f"{'ML':<20}"
        f"{ml_result['accuracy'] * 100:>11.2f}%"
        f"{ml_result['total']:>12}"
        f"{0:>14}"
    )

    print(
        f"{'Hybrid':<20}"
        f"{hybrid_result['accuracy'] * 100:>11.2f}%"
        f"{hybrid_result['resolved']:>12}"
        f"{hybrid_result['unresolved']:>14}"
    )

    print()
    print("Hybrid classification methods:")
    print("-" * 70)

    for method, count in sorted(
        hybrid_result["method_counts"].items()
    ):
        print(
            f"{method:<20}"
            f"{count:>10}"
        )


def print_hybrid_details(hybrid_result):
    """Print every benchmark example and its hybrid result."""

    print()
    print("=" * 70)
    print("HYBRID BENCHMARK DETAILS")
    print("=" * 70)

    for index, example in enumerate(
        GENERALIZATION_EXAMPLES,
        start=1,
    ):
        prediction = hybrid_result["predictions"][
            index - 1
        ]

        actual = hybrid_result["actual"][
            index - 1
        ]

        method = hybrid_result["methods"][
            index - 1
        ]

        confidence = hybrid_result["confidences"][
            index - 1
        ]

        correct = (
            prediction is not None
            and prediction == actual
        )

        print()
        print(f"{index}. {example.description}")
        print(f"   Actual:      {actual}")
        print(f"   Predicted:   {prediction}")
        print(f"   Method:      {method}")
        print(f"   Confidence:  {confidence:.2f}%")
        print(f"   Correct:     {correct}")


def main():
    print("=" * 70)
    print("HYBRID CLASSIFIER EVALUATION")
    print("=" * 70)

    transactions, _ = generate_dataset(
        n_users=5,
        months=12,
        seed=42,
    )

    print()
    print(
        f"Synthetic transactions: "
        f"{len(transactions)}"
    )

    print(
        "Generalization examples: "
        f"{len(GENERALIZATION_EXAMPLES)}"
    )

    # ---------------------------------------------------------
    # Rule-based evaluation
    # ---------------------------------------------------------

    rule_based_result = evaluate_rule_based(
        transactions
    )

    # ---------------------------------------------------------
    # Train ML model
    # ---------------------------------------------------------

    classifier = train_ml_classifier(
        transactions
    )

    # ---------------------------------------------------------
    # ML evaluation
    # ---------------------------------------------------------

    ml_result = evaluate_ml(
        classifier
    )

    # ---------------------------------------------------------
    # Hybrid evaluation
    # ---------------------------------------------------------

    hybrid_result = evaluate_hybrid(
        classifier
    )

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    print_summary(
        rule_based_result,
        ml_result,
        hybrid_result,
    )

    print()
    print("Rule-based method distribution:")
    print("-" * 70)

    for method, count in sorted(
        rule_based_result["methods"].items()
    ):
        print(
            f"{method:<20}"
            f"{count:>10}"
        )

    print()
    print("ML generalization benchmark:")
    print("-" * 70)

    print(
        f"Accuracy: "
        f"{ml_result['accuracy'] * 100:.2f}%"
    )

    print()
    print("Hybrid generalization benchmark:")
    print("-" * 70)

    print(
        f"Accuracy among resolved: "
        f"{hybrid_result['accuracy'] * 100:.2f}%"
    )

    print(
        f"Resolved: "
        f"{hybrid_result['resolved']}/"
        f"{hybrid_result['total']}"
    )

    print(
        f"Unresolved: "
        f"{hybrid_result['unresolved']}/"
        f"{hybrid_result['total']}"
    )

    print_hybrid_details(
        hybrid_result
    )


if __name__ == "__main__":
    main()
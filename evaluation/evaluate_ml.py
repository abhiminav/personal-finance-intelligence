from sklearn.metrics import accuracy_score, classification_report

from categorization.ml_classifier import MLClassifier
from evaluation.ml_dataset import get_ml_train_test_split


def main():
    (
        X_train,
        X_test,
        y_train,
        y_test,
    ) = get_ml_train_test_split()

    print("=" * 70)
    print("ML CLASSIFIER EVALUATION")
    print("=" * 70)

    print(f"Training samples: {len(X_train)}")
    print(f"Test samples:     {len(X_test)}")

    classifier = MLClassifier()

    classifier.fit(
        X_train,
        y_train,
    )

    predictions = classifier.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    print()
    print(f"Accuracy: {accuracy:.4f}")
    print()

    print("Classification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )


if __name__ == "__main__":
    main()
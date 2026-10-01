from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


@dataclass
class MLClassifier:
    """
    TF-IDF + Logistic Regression classifier for
    transaction-category prediction.
    """

    model: Pipeline | None = None

    def build_model(self) -> Pipeline:
        """
        Build the TF-IDF + Logistic Regression pipeline.
        """

        return Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        analyzer="char",
                        ngram_range=(2, 5),
                        min_df=1,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=1000,
                        random_state=42,
                    ),
                ),
            ]
        )

    def fit(
        self,
        descriptions: list[str],
        categories: list[str],
    ) -> None:
        """
        Train the classifier.
        """

        self.model = self.build_model()

        self.model.fit(
            descriptions,
            categories,
        )

    def predict(
        self,
        descriptions: list[str],
    ) -> list[str]:
        """
        Predict categories for transaction descriptions.
        """

        if self.model is None:
            raise RuntimeError(
                "Model must be fitted before prediction."
            )

        return self.model.predict(descriptions).tolist()

    def predict_proba(
        self,
        descriptions: list[str],
    ):
        """
        Return class probabilities for predictions.
        """

        if self.model is None:
            raise RuntimeError(
                "Model must be fitted before prediction."
            )

        return self.model.predict_proba(
            descriptions
        )


    def predict_with_confidence(
        self,
        descriptions: list[str],
    ) -> list[tuple[str, float]]:
        """
        Predict categories and return the model's
        confidence for each prediction.
        """

        if self.model is None:
            raise RuntimeError(
                "Model must be fitted before prediction."
            )

        probabilities = self.model.predict_proba(
            descriptions
        )

        predictions = self.model.predict(
            descriptions
        )

        results = []

        for prediction, probability_row in zip(
            predictions,
            probabilities,
        ):
            confidence = float(
                probability_row.max()
            )

            results.append(
                (prediction, confidence)
            )

        return results
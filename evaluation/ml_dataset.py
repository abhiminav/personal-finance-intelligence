from sklearn.model_selection import train_test_split

from data.synthetic_generator import generate_dataset


def get_ml_train_test_split(
    test_size: float = 0.20,
    random_state: int = 42,
):
    """
    Generate the synthetic transaction dataset and return
    a stratified train/test split for ML evaluation.
    """

    transactions, _ = generate_dataset(
        n_users=5,
        months=12,
        seed=42,
    )

    descriptions = [
        transaction.raw_description
        for transaction in transactions
    ]

    categories = [
        transaction.category
        for transaction in transactions
    ]

    (
        X_train,
        X_test,
        y_train,
        y_test,
    ) = train_test_split(
        descriptions,
        categories,
        test_size=test_size,
        random_state=random_state,
        stratify=categories,
    )

    return (
        X_train,
        X_test,
        y_train,
        y_test,
    )
from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryOverride:
    """
    Represents a user-defined category override.

    The override is keyed by a normalized merchant identity
    and stores the category selected by the user.
    """

    merchant_id: str
    category: str


class OverrideStore:
    """
    In-memory store for user-defined merchant category overrides.

    This is intentionally simple for the first implementation.
    Persistence can be added later when we introduce the
    application/database layer.
    """

    def __init__(self) -> None:
        self._overrides: dict[str, CategoryOverride] = {}

    def set_override(
        self,
        merchant_id: str,
        category: str,
    ) -> None:
        """
        Create or replace a merchant category override.
        """

        if not isinstance(merchant_id, str):
            raise TypeError(
                "merchant_id must be a string"
            )

        if not isinstance(category, str):
            raise TypeError(
                "category must be a string"
            )

        merchant_id = merchant_id.strip()
        category = category.strip()

        if not merchant_id:
            raise ValueError(
                "merchant_id cannot be empty"
            )

        if not category:
            raise ValueError(
                "category cannot be empty"
            )

        self._overrides[merchant_id] = CategoryOverride(
            merchant_id=merchant_id,
            category=category,
        )

    def get_override(
        self,
        merchant_id: str,
    ) -> str | None:
        """
        Return the overridden category for a merchant.

        Returns None when no override exists.
        """

        if not isinstance(merchant_id, str):
            raise TypeError(
                "merchant_id must be a string"
            )

        override = self._overrides.get(
            merchant_id.strip()
        )

        if override is None:
            return None

        return override.category

    def has_override(
        self,
        merchant_id: str,
    ) -> bool:
        """
        Return True when a merchant has an override.
        """

        return self.get_override(merchant_id) is not None

    def remove_override(
        self,
        merchant_id: str,
    ) -> bool:
        """
        Remove a merchant override.

        Returns True if an override was removed,
        otherwise False.
        """

        if not isinstance(merchant_id, str):
            raise TypeError(
                "merchant_id must be a string"
            )

        merchant_id = merchant_id.strip()

        if merchant_id in self._overrides:
            del self._overrides[merchant_id]
            return True

        return False

    def get_all_overrides(
        self,
    ) -> list[CategoryOverride]:
        """
        Return all configured overrides.
        """

        return list(self._overrides.values())
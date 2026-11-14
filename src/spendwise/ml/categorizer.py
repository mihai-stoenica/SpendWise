"""Category suggestion baseline and scikit-learn implementations skeleton."""


class BaselineCategoryPredictor:
    """No-op / baseline category predictor."""

    def suggest(self, text: str) -> tuple[str, float] | None:
        """Return no suggestion."""
        return None

    def learn(self, text: str, category: str) -> None:
        """No-op learning."""
        pass

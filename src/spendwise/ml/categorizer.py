class BaselineCategoryPredictor:
    def suggest(self, text: str) -> tuple[str, float] | None:
        return None

    def learn(self, text: str, category: str) -> None:
        pass


class LevelizedCostModel:
    """
    Generic levelized cost model using already-discounted totals.
    """

    def __init__(self):
        self.discounted_numerator_total = None
        self.discounted_denominator_total = None
        self.levelized_cost = None

    def configure(self, config):
        self.discounted_numerator_total = config.get("discounted_numerator_total", 0.0)
        self.discounted_denominator_total = config.get("discounted_denominator_total", 0.0)

    def evaluate(self):
        if self.discounted_denominator_total is None or self.discounted_denominator_total <= 0:
            raise ValueError("discounted_denominator_total must be greater than zero.")

        self.levelized_cost = (
            self.discounted_numerator_total / self.discounted_denominator_total
        )

        return {
            "discounted_numerator_total": self.discounted_numerator_total,
            "discounted_denominator_total": self.discounted_denominator_total,
            "levelized_cost": self.levelized_cost,
        }
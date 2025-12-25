from dataclasses import dataclass

@dataclass(frozen=True)
class PricingInput:
    spot: float
    strike: float
    t_expiry_years: float
    rate: float
    div_yield: float
    vol: float
    is_call: bool

    def validate(self):
        assert all(map(lambda x: isinstance(x, float), [self.spot, self.strike, self.t_expiry_years, self.rate, self.div_yield, self.vol]))
        assert self.t_expiry_years >= 0
        assert self.vol >= 0
        assert self.spot > 0 and self.strike > 0
        assert isinstance(self.is_call, bool)

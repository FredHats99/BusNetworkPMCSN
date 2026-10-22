"""Student intervals for replica statistics; stdlib only.

Incomplete beta continued fraction: NIST DLMF 8.17(v). No per-traversal iid
assumption. Bonferroni family size is supplied by the fixed assertion inventory.
"""
import functools
import math
import statistics


def _beta_fraction(a, b, x):
    tiny = 1e-300

    def nonzero(v):
        return v if abs(v) >= tiny else math.copysign(tiny, v)

    c = 1.0
    d = 1.0 / nonzero(1.0 - (a+b)*x/(a+1.0))
    value = d
    for m in range(1, 10001):
        for coefficient in (m*(b-m)*x/((a+2*m-1)*(a+2*m)),
                            -(a+m)*(a+b+m)*x/((a+2*m)*(a+2*m+1))):
            d = 1.0 / nonzero(1.0 + coefficient*d)
            c = nonzero(1.0 + coefficient/c)
            change = c*d
            value *= change
        if abs(change-1.0) < 3e-14:
            return value
    raise ArithmeticError("Incomplete beta fraction did not converge")


def beta_regularized(x, a, b):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    if x > (a+1)/(a+b+2):
        return 1-beta_regularized(1-x, b, a)
    front = math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    return front*_beta_fraction(a, b, x)/a


def student_upper_tail(t, df):
    if df <= 0 or t < 0:
        raise ValueError("Positive degrees of freedom and nonnegative t required")
    return .5*beta_regularized(df/(df+t*t), df/2, .5)


@functools.lru_cache(maxsize=4096)
def student_critical(df, tail):
    if not 0 < tail < .5:
        raise ValueError("Invalid Student tail")
    low, high = 0.0, 1.0
    while student_upper_tail(high, df) > tail:
        high *= 2
        if high > 1e12:
            raise ArithmeticError("Student quantile could not be bracketed")
    for _ in range(90):
        middle = (low+high)/2
        if student_upper_tail(middle, df) > tail:
            low = middle
        else:
            high = middle
    return (low+high)/2


def assess(values, target, margin, family_size, confidence, required):
    complete = len(values) == required and all(v is not None and math.isfinite(v) for v in values)
    valid = [v for v in values if v is not None and math.isfinite(v)]
    result = {"available_replicas": len(valid), "required_replicas": required,
              "target": target, "margin": margin, "status": "inconclusive", "reason": "insufficient_coverage"}
    if not complete:
        return result
    centered = [v-target for v in valid]
    mean = statistics.fmean(centered)
    se = statistics.stdev(centered)/math.sqrt(len(centered))
    critical = student_critical(len(centered)-1, (1-confidence)/(2*family_size))
    low, high = mean-critical*se, mean+critical*se
    status = "passed" if low > -margin and high < margin else "failed" if low > margin or high < -margin else "inconclusive"
    result.update(status=status, reason="equivalent" if status == "passed" else "outside_margin" if status == "failed" else "insufficient_precision",
                  mean=mean+target, deviation=mean, standard_error=se, interval_deviation=[low, high], critical_value=critical,
                  replica_sd=statistics.stdev(valid), replica_min=min(valid), replica_max=max(valid))
    return result

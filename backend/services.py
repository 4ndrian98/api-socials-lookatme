from typing import Iterable
from models import Rilevazione

def _to_float(x):
    return float(x) if x is not None else None

def compute_sentiment(r: Rilevazione | None) -> float | None:
    if not r: return None
    gioia = _to_float(r.gioia) or 0.0
    negativi = [_to_float(r.tristezza), _to_float(r.paura), _to_float(r.rabbia), _to_float(r.disgusto)]
    neg = sum([v for v in negativi if v is not None]) / max(1, len([v for v in negativi if v is not None]))
    # score semplice 0..1
    score = max(0.0, min(1.0, 0.5 + (gioia - (neg or 0.0))))
    return round(score, 2)

def sentiment_trend(rilevazioni: Iterable[Rilevazione], last_n: int = 7) -> list[float]:
    arr = list(rilevazioni)[-last_n:]
    return [compute_sentiment(r) or 0.5 for r in arr]

def build_suggestions(sentiment: float | None, trend: list[float]) -> list[str]:
    s = sentiment if sentiment is not None else 0.5
    tips = []
    if s < 0.4:
        tips.append("Attiva campagne social mirate e rispondi a recensioni negative.")
    if trend and len(trend) >= 3 and trend[-1] < trend[0]:
        tips.append("Il sentiment è in calo: pubblica contenuti positivi e offerte.")
    if s > 0.7:
        tips.append("Molto bene! Mantieni la frequenza dei post e incoraggia le recensioni.")
    if not tips:
        tips.append("Mantieni costanza nella comunicazione e monitora i KPI settimanali.")
    return tips

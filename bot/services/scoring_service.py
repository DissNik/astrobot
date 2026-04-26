from dataclasses import dataclass

from bot.domain.enums import ObservingProfile, SkyPreset

PERCENT_MIN = 0
PERCENT_MAX = 100
MOON_PHASE_MIN = 0
MOON_PHASE_MAX = 1
WIND_SPEED_MIN = 0
BORTLE_MIN = 1
BORTLE_MAX = 9

CLOUD_COVER_WEIGHT = 0.45
HIGH_CLOUD_COVER_WEIGHT = 0.15
CLEAR_CLOUD_COVER_THRESHOLD = 20
HIGH_CLOUD_COVER_THRESHOLD = 45
CLOUDY_THRESHOLD = 60
SEVERE_CLOUD_COVER_THRESHOLD = 80
SEVERE_CLOUD_COVER_PENALTY = 15

DEEP_SKY_MOON_PHASE_WEIGHT = 20
VISIBLE_MOON_PENALTY = 10
MOON_REASON_THRESHOLD = 15
DARK_SITE_BORTLE_BASELINE = 3
BORTLE_PENALTY_WEIGHT = 4
BRIGHT_SKY_BORTLE_THRESHOLD = 7

HIGH_HUMIDITY_THRESHOLD = 85
HIGH_HUMIDITY_PENALTY = 10
MODERATE_HUMIDITY_THRESHOLD = 75
MODERATE_HUMIDITY_PENALTY = 5
FOG_RISK_THRESHOLD = 60
FOG_RISK_PENALTY = 12
STRONG_WIND_THRESHOLD = 10
STRONG_WIND_PENALTY = 10
MODERATE_WIND_THRESHOLD = 6
MODERATE_WIND_PENALTY = 5

EXCELLENT_SCORE_THRESHOLD = 80
GOOD_SCORE_THRESHOLD = 60
DOUBTFUL_SCORE_THRESHOLD = 40
MIN_SCORE = 0
MAX_SCORE = 100


@dataclass(frozen=True)
class ScoreInput:
    profile: ObservingProfile
    cloud_cover: int
    high_cloud_cover: int
    moon_phase: float
    moon_visible: bool
    humidity: int
    fog_risk: int
    wind_speed: float
    sky_preset: SkyPreset
    bortle_class: int | None

    def __post_init__(self) -> None:
        _validate_range("cloud_cover", self.cloud_cover, PERCENT_MIN, PERCENT_MAX)
        _validate_range("high_cloud_cover", self.high_cloud_cover, PERCENT_MIN, PERCENT_MAX)
        _validate_range("humidity", self.humidity, PERCENT_MIN, PERCENT_MAX)
        _validate_range("fog_risk", self.fog_risk, PERCENT_MIN, PERCENT_MAX)
        _validate_range("moon_phase", self.moon_phase, MOON_PHASE_MIN, MOON_PHASE_MAX)
        if self.wind_speed < WIND_SPEED_MIN:
            raise ValueError("wind_speed must be greater than or equal to 0")
        if self.bortle_class is not None:
            _validate_range("bortle_class", self.bortle_class, BORTLE_MIN, BORTLE_MAX)


@dataclass(frozen=True)
class ScoreResult:
    score: int
    verdict: str
    reasons: tuple[str, ...]


def score_conditions(data: ScoreInput) -> ScoreResult:
    score = 100
    reasons: list[str] = []

    cloud_penalty = round(data.cloud_cover * CLOUD_COVER_WEIGHT)
    score -= cloud_penalty
    if data.cloud_cover >= CLOUDY_THRESHOLD:
        reasons.append("высокая общая облачность")
        if data.cloud_cover >= SEVERE_CLOUD_COVER_THRESHOLD:
            score -= SEVERE_CLOUD_COVER_PENALTY
    elif data.cloud_cover <= CLEAR_CLOUD_COVER_THRESHOLD:
        reasons.append("мало облаков")

    high_cloud_penalty = round(data.high_cloud_cover * HIGH_CLOUD_COVER_WEIGHT)
    score -= high_cloud_penalty
    if data.high_cloud_cover >= HIGH_CLOUD_COVER_THRESHOLD:
        reasons.append("много высокой облачности")

    if data.profile is ObservingProfile.DEEP_SKY:
        moon_penalty = round(data.moon_phase * DEEP_SKY_MOON_PHASE_WEIGHT)
        if data.moon_visible:
            moon_penalty += VISIBLE_MOON_PENALTY
        score -= moon_penalty
        if moon_penalty >= MOON_REASON_THRESHOLD:
            reasons.append("Луна мешает deep-sky")

        bortle = data.bortle_class or _preset_bortle(data.sky_preset)
        sky_penalty = max(0, bortle - DARK_SITE_BORTLE_BASELINE) * BORTLE_PENALTY_WEIGHT
        score -= sky_penalty
        if bortle >= BRIGHT_SKY_BORTLE_THRESHOLD:
            reasons.append("светлое небо")
    else:
        if data.moon_visible:
            reasons.append("Луна не критична для планет")

    if data.humidity >= HIGH_HUMIDITY_THRESHOLD:
        score -= HIGH_HUMIDITY_PENALTY
        reasons.append("высокая влажность")
    elif data.humidity >= MODERATE_HUMIDITY_THRESHOLD:
        score -= MODERATE_HUMIDITY_PENALTY
        reasons.append("умеренно высокая влажность")

    if data.fog_risk >= FOG_RISK_THRESHOLD:
        score -= FOG_RISK_PENALTY
        reasons.append("риск тумана")

    if data.wind_speed >= STRONG_WIND_THRESHOLD:
        score -= STRONG_WIND_PENALTY
        reasons.append("сильный ветер")
    elif data.wind_speed >= MODERATE_WIND_THRESHOLD:
        score -= MODERATE_WIND_PENALTY
        reasons.append("умеренный ветер")

    score = max(MIN_SCORE, min(MAX_SCORE, score))
    return ScoreResult(score=score, verdict=_verdict(score), reasons=tuple(reasons))


def _validate_range(name: str, value: int | float, minimum: int, maximum: int) -> None:
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")


def _preset_bortle(preset: SkyPreset) -> int:
    return {
        SkyPreset.CITY: 8,
        SkyPreset.SUBURB: 6,
        SkyPreset.DARK_SITE: 3,
        SkyPreset.CUSTOM_BORTLE: 5,
    }[preset]


def _verdict(score: int) -> str:
    if score >= EXCELLENT_SCORE_THRESHOLD:
        return "отлично"
    if score >= GOOD_SCORE_THRESHOLD:
        return "можно ехать"
    if score >= DOUBTFUL_SCORE_THRESHOLD:
        return "сомнительно"
    return "не стоит"

from dataclasses import dataclass

from bot.domain.enums import ObservingProfile, SkyPreset


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


@dataclass(frozen=True)
class ScoreResult:
    score: int
    verdict: str
    reasons: list[str]


def score_conditions(data: ScoreInput) -> ScoreResult:
    score = 100
    reasons: list[str] = []

    cloud_penalty = round(data.cloud_cover * 0.45)
    score -= cloud_penalty
    if data.cloud_cover >= 60:
        reasons.append("высокая общая облачность")
        if data.cloud_cover >= 80:
            score -= 15
    elif data.cloud_cover <= 20:
        reasons.append("мало облаков")

    high_cloud_penalty = round(data.high_cloud_cover * 0.15)
    score -= high_cloud_penalty
    if data.high_cloud_cover >= 45:
        reasons.append("много высокой облачности")

    if data.profile is ObservingProfile.DEEP_SKY:
        moon_penalty = round(data.moon_phase * 20)
        if data.moon_visible:
            moon_penalty += 10
        score -= moon_penalty
        if moon_penalty >= 15:
            reasons.append("Луна мешает deep-sky")

        bortle = data.bortle_class or _preset_bortle(data.sky_preset)
        sky_penalty = max(0, bortle - 3) * 4
        score -= sky_penalty
        if bortle >= 7:
            reasons.append("светлое небо")
    else:
        if data.moon_visible:
            reasons.append("Луна не критична для планет")

    if data.humidity >= 85:
        score -= 10
        reasons.append("высокая влажность")
    elif data.humidity >= 75:
        score -= 5
        reasons.append("умеренно высокая влажность")

    if data.fog_risk >= 60:
        score -= 12
        reasons.append("риск тумана")

    if data.wind_speed >= 10:
        score -= 10
        reasons.append("сильный ветер")
    elif data.wind_speed >= 6:
        score -= 5
        reasons.append("умеренный ветер")

    score = max(0, min(100, score))
    return ScoreResult(score=score, verdict=_verdict(score), reasons=reasons)


def _preset_bortle(preset: SkyPreset) -> int:
    return {
        SkyPreset.CITY: 8,
        SkyPreset.SUBURB: 6,
        SkyPreset.DARK_SITE: 3,
        SkyPreset.CUSTOM_BORTLE: 5,
    }[preset]


def _verdict(score: int) -> str:
    if score >= 80:
        return "отлично"
    if score >= 60:
        return "можно ехать"
    if score >= 40:
        return "сомнительно"
    return "не стоит"

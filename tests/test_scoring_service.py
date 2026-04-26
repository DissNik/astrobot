import pytest

from bot.domain.enums import ObservingProfile, SkyPreset
from bot.services.scoring_service import ScoreInput, _verdict, score_conditions


def _valid_score_input(**overrides: object) -> ScoreInput:
    values = {
        "profile": ObservingProfile.DEEP_SKY,
        "cloud_cover": 10,
        "high_cloud_cover": 5,
        "moon_phase": 0.1,
        "moon_visible": False,
        "humidity": 55,
        "fog_risk": 0,
        "wind_speed": 3,
        "sky_preset": SkyPreset.DARK_SITE,
        "bortle_class": 3,
    }
    values.update(overrides)
    return ScoreInput(**values)


def test_clear_dark_deep_sky_night_scores_high() -> None:
    result = score_conditions(_valid_score_input())

    assert result.score >= 85
    assert result.verdict == "отлично"


def test_cloudy_night_scores_low() -> None:
    result = score_conditions(
        ScoreInput(
            profile=ObservingProfile.DEEP_SKY,
            cloud_cover=85,
            high_cloud_cover=70,
            moon_phase=0.2,
            moon_visible=False,
            humidity=60,
            fog_risk=0,
            wind_speed=4,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=3,
        )
    )

    assert result.score <= 35
    assert result.verdict == "не стоит"
    assert any("облачность" in reason for reason in result.reasons)


def test_full_moon_penalizes_deep_sky_more_than_planetary() -> None:
    common = dict(
        cloud_cover=15,
        high_cloud_cover=5,
        moon_phase=0.98,
        moon_visible=True,
        humidity=55,
        fog_risk=0,
        wind_speed=3,
        sky_preset=SkyPreset.DARK_SITE,
        bortle_class=3,
    )

    deep_sky = score_conditions(ScoreInput(profile=ObservingProfile.DEEP_SKY, **common))
    planetary = score_conditions(ScoreInput(profile=ObservingProfile.PLANETARY_LUNAR, **common))

    assert planetary.score > deep_sky.score


def test_city_sky_penalizes_deep_sky() -> None:
    dark = score_conditions(
        ScoreInput(
            profile=ObservingProfile.DEEP_SKY,
            cloud_cover=15,
            high_cloud_cover=5,
            moon_phase=0.1,
            moon_visible=False,
            humidity=55,
            fog_risk=0,
            wind_speed=3,
            sky_preset=SkyPreset.DARK_SITE,
            bortle_class=3,
        )
    )
    city = score_conditions(
        ScoreInput(
            profile=ObservingProfile.DEEP_SKY,
            cloud_cover=15,
            high_cloud_cover=5,
            moon_phase=0.1,
            moon_visible=False,
            humidity=55,
            fog_risk=0,
            wind_speed=3,
            sky_preset=SkyPreset.CITY,
            bortle_class=8,
        )
    )

    assert city.score < dark.score


def test_score_result_reasons_are_immutable_tuple() -> None:
    result = score_conditions(_valid_score_input())

    assert isinstance(result.reasons, tuple)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("cloud_cover", -1, "cloud_cover must be between 0 and 100"),
        ("cloud_cover", 101, "cloud_cover must be between 0 and 100"),
        ("high_cloud_cover", -1, "high_cloud_cover must be between 0 and 100"),
        ("high_cloud_cover", 101, "high_cloud_cover must be between 0 and 100"),
        ("humidity", -1, "humidity must be between 0 and 100"),
        ("humidity", 101, "humidity must be between 0 and 100"),
        ("fog_risk", -1, "fog_risk must be between 0 and 100"),
        ("fog_risk", 101, "fog_risk must be between 0 and 100"),
        ("moon_phase", -0.1, "moon_phase must be between 0 and 1"),
        ("moon_phase", 1.1, "moon_phase must be between 0 and 1"),
        ("wind_speed", -0.1, "wind_speed must be greater than or equal to 0"),
        ("bortle_class", 0, "bortle_class must be between 1 and 9"),
        ("bortle_class", 10, "bortle_class must be between 1 and 9"),
    ],
)
def test_score_input_validates_physical_ranges(
    field: str, value: int | float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _valid_score_input(**{field: value})


def test_score_input_allows_missing_bortle_class() -> None:
    data = _valid_score_input(bortle_class=None)

    assert data.bortle_class is None


@pytest.mark.parametrize(
    ("score", "verdict"),
    [
        (100, "отлично"),
        (80, "отлично"),
        (79, "можно ехать"),
        (60, "можно ехать"),
        (59, "сомнительно"),
        (40, "сомнительно"),
        (39, "не стоит"),
        (0, "не стоит"),
    ],
)
def test_verdict_boundaries(score: int, verdict: str) -> None:
    assert _verdict(score) == verdict

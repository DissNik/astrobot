from bot.domain.enums import ObservingProfile, SkyPreset
from bot.services.scoring_service import ScoreInput, score_conditions


def test_clear_dark_deep_sky_night_scores_high() -> None:
    result = score_conditions(
        ScoreInput(
            profile=ObservingProfile.DEEP_SKY,
            cloud_cover=10,
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

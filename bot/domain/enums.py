from enum import StrEnum


class ObservingProfile(StrEnum):
    DEEP_SKY = "deep_sky"
    PLANETARY_LUNAR = "planetary_lunar"


class SubscriptionMode(StrEnum):
    DAILY_DIGEST = "daily_digest"
    GOOD_CONDITIONS_ONLY = "good_conditions_only"


class LocationSource(StrEnum):
    CITY = "city"
    COORDINATES = "coordinates"
    TELEGRAM_GEO = "telegram_geo"


class SkyPreset(StrEnum):
    CITY = "city"
    SUBURB = "suburb"
    DARK_SITE = "dark_site"
    CUSTOM_BORTLE = "custom_bortle"

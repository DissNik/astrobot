DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en", "ru"}


TEXTS = {
    "en": {
        "forecast_title": "Astronomical forecast",
        "no_forecasts": "No forecasts available.",
        "location": "Location",
        "cloud_cover": "Cloud cover",
        "high_cloud_cover": "high",
        "moon": "Moon",
        "visible": "visible",
        "not_visible": "not visible",
        "humidity": "Humidity",
        "wind": "Wind",
        "reasons": "Reasons",
        "no_reasons": "no notable factors",
        "settings_title": "Profile and subscription settings.",
        "forecast_days": "Forecast horizon",
        "nights": "nights",
        "observing_profile": "Observing profile",
        "subscription": "Subscription",
        "enabled": "enabled",
        "disabled": "disabled",
        "send_time": "Notification time",
        "subscription_mode": "Notification mode",
        "threshold": "Good conditions threshold",
        "daily_digest": "daily digest",
        "good_conditions_only": "good conditions only",
        "deep_sky": "deep-sky",
        "planetary_lunar": "planetary/lunar",
        "choose_location": "Choose an observing location for the forecast.",
        "add_location_first": "Add an observing location in Locations first.",
        "location_not_found": "I could not find this observing location. Open forecast again.",
        "forecast_error": "Could not get the forecast. Try again later.",
        "enter_send_time": "Enter notification time in HH:MM format.",
        "send_time_updated": "Notification time updated.",
        "invalid_send_time": (
            "Could not parse the time. Enter it in HH:MM format, for example 21:30."
        ),
        "language_updated": "Language updated.",
        "days_updated": "Forecast horizon updated.",
        "profile_updated": "Observing profile updated.",
        "threshold_updated": "Good conditions threshold updated.",
        "mode_updated": "Notification mode updated.",
    },
    "ru": {
        "forecast_title": "Астрономический прогноз",
        "no_forecasts": "Нет доступных прогнозов.",
        "location": "Локация",
        "cloud_cover": "Облачность",
        "high_cloud_cover": "высокая",
        "moon": "Луна",
        "visible": "видна",
        "not_visible": "не видна",
        "humidity": "Влажность",
        "wind": "Ветер",
        "reasons": "Причины",
        "no_reasons": "нет заметных факторов",
        "settings_title": "Настройки профиля и рассылки.",
        "forecast_days": "Горизонт прогноза",
        "nights": "ночи",
        "observing_profile": "Профиль наблюдений",
        "subscription": "Рассылка",
        "enabled": "включена",
        "disabled": "отключена",
        "send_time": "Время рассылки",
        "subscription_mode": "Режим рассылки",
        "threshold": "Порог хороших условий",
        "daily_digest": "ежедневный дайджест",
        "good_conditions_only": "только хорошие условия",
        "deep_sky": "deep-sky",
        "planetary_lunar": "планеты/Луна",
        "choose_location": "Выберите локацию наблюдения для прогноза.",
        "add_location_first": "Сначала добавьте локацию наблюдения в разделе «Локации».",
        "location_not_found": "Не нашел эту локацию наблюдения. Откройте прогноз заново.",
        "forecast_error": "Не удалось получить прогноз. Попробуйте позже.",
        "enter_send_time": "Введите время рассылки в формате HH:MM.",
        "send_time_updated": "Время рассылки обновлено.",
        "invalid_send_time": (
            "Не смог разобрать время. Введите время в формате HH:MM, например 21:30."
        ),
        "language_updated": "Язык обновлен.",
        "days_updated": "Горизонт прогноза обновлен.",
        "profile_updated": "Профиль наблюдений обновлен.",
        "threshold_updated": "Порог хороших условий обновлен.",
        "mode_updated": "Режим рассылки обновлен.",
    },
}

VERDICTS = {
    "en": {
        "отлично": "excellent",
        "можно ехать": "good to go",
        "сомнительно": "questionable",
        "не стоит": "not worth it",
    },
    "ru": {},
}

REASONS = {
    "en": {
        "высокая общая облачность": "high total cloud cover",
        "мало облаков": "low cloud cover",
        "много высокой облачности": "lots of high cloud cover",
        "Луна мешает deep-sky": "Moon interferes with deep-sky",
        "светлое небо": "bright sky",
        "Луна не критична для планет": "Moon is not critical for planets",
        "высокая влажность": "high humidity",
        "умеренно высокая влажность": "moderately high humidity",
        "риск тумана": "fog risk",
        "сильный ветер": "strong wind",
        "умеренный ветер": "moderate wind",
    },
    "ru": {},
}


def normalize_language(language: str | None) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language
    return DEFAULT_LANGUAGE


def text(key: str, language: str | None = None) -> str:
    active_language = normalize_language(language)
    return TEXTS[active_language][key]


def translate_verdict(verdict: str, language: str | None = None) -> str:
    active_language = normalize_language(language)
    return VERDICTS.get(active_language, {}).get(verdict, verdict)


def translate_reason(reason: str, language: str | None = None) -> str:
    active_language = normalize_language(language)
    return REASONS.get(active_language, {}).get(reason, reason)

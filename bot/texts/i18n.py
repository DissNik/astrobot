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
        "main_menu": "Main menu",
        "start_text": "Hi! I will help you choose the best time for an astronomy trip.",
        "menu_forecast": "🔭 Forecast",
        "menu_locations": "📍 Locations",
        "menu_subscription": "📬 Alerts",
        "menu_settings": "⚙️ Settings",
        "enter_send_time": "Enter notification time and timezone, for example 21:30 Europe/Moscow.",
        "send_time_updated": "Notification time updated.",
        "invalid_send_time": (
            "Could not parse the time. Enter time and timezone, for example "
            "21:30 Europe/Moscow."
        ),
        "language_updated": "Language updated.",
        "language_set_en": "English language is set.",
        "language_set_ru": "Russian language is set.",
        "days_updated": "Forecast horizon updated.",
        "profile_updated": "Observing profile updated.",
        "threshold_updated": "Good conditions threshold updated.",
        "mode_updated": "Notification mode updated.",
        "settings_days_3": "3 nights",
        "settings_days_5": "5 nights",
        "settings_days_7": "7 nights",
        "settings_language_en": "English",
        "settings_language_ru": "Русский",
        "settings_profile_deep_sky": "Deep-sky",
        "settings_profile_planetary_lunar": "Planetary/Lunar",
        "settings_daily_digest": "Daily digest",
        "settings_good_conditions_only": "Good conditions only",
        "settings_threshold_50": "Threshold 50",
        "settings_threshold_60": "Threshold 60",
        "settings_threshold_70": "Threshold 70",
        "settings_threshold_80": "Threshold 80",
        "locations_text": "Observing locations. Manage your saved places here.",
        "add_location": "Add location",
        "my_locations": "My locations",
        "add_location_prompt": (
            "Send a city, coordinates like 45.0448, 38.976, or a Telegram location."
        ),
        "invalid_location_input": (
            "I could not find the location. Send a city, coordinates, or a Telegram location."
        ),
        "location_name_prompt": "Enter the location name.",
        "invalid_location_name": "Location name must not be empty.",
        "location_not_found_short": "I could not find this location. Open the location list again.",
        "rename_location_prompt": "Enter a new location name.",
        "location_saved": "Location saved: {name}",
        "location_renamed": "Location renamed: {name}",
        "location_deleted": "Location deleted.",
        "location_alerts_enabled": "Location enabled for alerts.",
        "location_alerts_disabled": "Location disabled for alerts.",
        "no_saved_locations": "You do not have saved locations yet.",
        "your_locations": "Your locations:",
        "coordinates": "Coordinates",
        "source": "Source",
        "alerts": "Alerts",
        "source_city": "city",
        "source_coordinates": "coordinates",
        "source_telegram_geo": "Telegram location",
        "location_default_name": "Location {latitude:.4f}, {longitude:.4f}",
        "rename": "Rename",
        "enable_alerts": "Enable alerts",
        "disable_alerts": "Disable alerts",
        "delete": "Delete",
        "back": "Back",
        "back_to_list": "Back to list",
        "subscription_text": (
            "Astronomy forecast alerts. You can enable a daily digest or disable sending."
        ),
        "subscription_enabled_message": (
            "Alerts enabled. I will send a daily digest at {send_time} {timezone}."
        ),
        "subscription_disabled_message": "Alerts disabled.",
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
        "main_menu": "Главное меню",
        "start_text": "Привет! Я помогу выбрать лучшее время для астрономической поездки.",
        "menu_forecast": "🔭 Прогноз",
        "menu_locations": "📍 Локации",
        "menu_subscription": "📬 Рассылка",
        "menu_settings": "⚙️ Настройки",
        "enter_send_time": (
            "Введите время рассылки и часовой пояс, например 21:30 Europe/Moscow."
        ),
        "send_time_updated": "Время рассылки обновлено.",
        "invalid_send_time": (
            "Не смог разобрать время. Введите время и часовой пояс, например "
            "21:30 Europe/Moscow."
        ),
        "language_updated": "Язык обновлен.",
        "language_set_en": "Установлен английский язык.",
        "language_set_ru": "Установлен русский язык.",
        "days_updated": "Горизонт прогноза обновлен.",
        "profile_updated": "Профиль наблюдений обновлен.",
        "threshold_updated": "Порог хороших условий обновлен.",
        "mode_updated": "Режим рассылки обновлен.",
        "settings_days_3": "3 ночи",
        "settings_days_5": "5 ночей",
        "settings_days_7": "7 ночей",
        "settings_language_en": "English",
        "settings_language_ru": "Русский",
        "settings_profile_deep_sky": "Deep-sky",
        "settings_profile_planetary_lunar": "Планеты/Луна",
        "settings_daily_digest": "Ежедневный дайджест",
        "settings_good_conditions_only": "Только хорошие условия",
        "settings_threshold_50": "Порог 50",
        "settings_threshold_60": "Порог 60",
        "settings_threshold_70": "Порог 70",
        "settings_threshold_80": "Порог 80",
        "locations_text": "Локации наблюдения. Здесь можно управлять сохраненными местами.",
        "add_location": "Добавить локацию",
        "my_locations": "Мои локации",
        "add_location_prompt": (
            "Отправьте город, координаты вида 45.0448, 38.976 или геолокацию Telegram."
        ),
        "invalid_location_input": (
            "Не нашел локацию. Отправьте город, координаты или геолокацию Telegram."
        ),
        "location_name_prompt": "Введите название локации.",
        "invalid_location_name": "Название локации не должно быть пустым.",
        "location_not_found_short": "Не нашел эту локацию. Откройте список локаций заново.",
        "rename_location_prompt": "Введите новое название локации.",
        "location_saved": "Локация сохранена: {name}",
        "location_renamed": "Локация переименована: {name}",
        "location_deleted": "Локация удалена.",
        "location_alerts_enabled": "Локация включена для рассылки.",
        "location_alerts_disabled": "Локация отключена от рассылки.",
        "no_saved_locations": "У вас пока нет сохраненных локаций.",
        "your_locations": "Ваши локации:",
        "coordinates": "Координаты",
        "source": "Источник",
        "alerts": "Рассылка",
        "source_city": "город",
        "source_coordinates": "координаты",
        "source_telegram_geo": "геолокация Telegram",
        "location_default_name": "Локация {latitude:.4f}, {longitude:.4f}",
        "rename": "Переименовать",
        "enable_alerts": "Включить рассылку",
        "disable_alerts": "Отключить рассылку",
        "delete": "Удалить",
        "back": "Назад",
        "back_to_list": "Назад к списку",
        "subscription_text": (
            "Рассылка астрономического прогноза. Можно включить ежедневный дайджест "
            "или отключить отправку."
        ),
        "subscription_enabled_message": (
            "Рассылка включена. Я отправлю ежедневный дайджест в {send_time} {timezone}."
        ),
        "subscription_disabled_message": "Рассылка отключена.",
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

# Manual Test Checklist

- [ ] `/start` shows the main menu.
- [ ] `/locations` opens location management.
- [ ] Adding a city location resolves at least one geocoding candidate.
- [ ] Adding coordinates stores the expected latitude and longitude.
- [ ] Adding Telegram geolocation stores the expected coordinates.
- [ ] Location can be renamed.
- [ ] Location can be enabled and disabled for subscription.
- [ ] `/forecast` returns a 3-night forecast by default.
- [ ] Forecast horizon can be changed to 5 and 7 nights.
- [ ] Observing profile can be changed between deep-sky and planetary/lunar.
- [ ] Subscription can be enabled and disabled.
- [ ] Daily digest mode sends a message at the configured local time.
- [ ] Good-conditions-only mode sends only when a score reaches the threshold.
- [ ] `/stats` works for `OWNER_TELEGRAM_ID`.
- [ ] `/stats` is rejected for non-owner users.
- [ ] Bot continues running if Open-Meteo returns an error.

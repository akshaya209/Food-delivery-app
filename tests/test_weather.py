from app.weather import format_weather

def test_format_weather():
    assert format_weather("Bangalore", 28) == "The weather in Bangalore is 28°C"

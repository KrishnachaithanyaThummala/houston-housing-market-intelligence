from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


def test_every_page_and_property_journey():
    app=AppTest.from_file(str(ROOT/'app.py'), default_timeout=90).run()
    assert not app.exception
    for page in ['Housing map','Property intelligence','Market forecasting','Housing assistant','Model evaluation','Data & methodology']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page,app.exception)
    app.sidebar.radio[0].set_value('Housing assistant').run()
    app.text_input[0].set_value('What is the historical listing price?').run()
    assert not app.exception
    assert any('historical asking price was' in item.value for item in app.markdown)


def test_empty_filters_keep_forecasts_available():
    app=AppTest.from_file(str(ROOT/'app.py'), default_timeout=90).run()
    app.sidebar.multiselect[0].set_value([]).run()
    app.sidebar.radio[0].set_value('Market forecasting').run()
    assert not app.exception

from streamlit_app import _advanced_defaults


def test_advanced_options_defaults_are_hidden_friendly():
    defaults = _advanced_defaults()

    assert defaults["include_artifacts"] is False
    assert defaults["documentation_mode"] == "auto"
    assert defaults["doc_max_pages"] == 40
    assert defaults["doc_max_depth"] == 2

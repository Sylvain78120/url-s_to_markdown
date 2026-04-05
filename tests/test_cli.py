from url_s_to_markdown.cli import main


def test_main_returns_error_when_no_url(capsys):
    code = main([])
    captured = capsys.readouterr()

    assert code == 1
    assert "Total détectées" in captured.out
    assert "aucune URL valide" in captured.out

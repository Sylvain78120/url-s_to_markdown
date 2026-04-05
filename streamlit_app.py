"""Interface web Streamlit pour url-s_to_markdown."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from url_s_to_markdown.http_client import UrllibHTTPClient
from url_s_to_markdown.inputs import parse_url_stats_from_candidates, parse_urls_from_text_block
from url_s_to_markdown.pipeline import run_pipeline


def _get_candidates(mode: str, single_url: str, pasted_urls: str, uploaded_file) -> list[str]:
    if mode == "URL unique":
        return [single_url.strip()] if single_url.strip() else []

    if mode == "Liste collée":
        return parse_urls_from_text_block(pasted_urls)

    if mode == "Fichier uploadé":
        if uploaded_file is None:
            return []
        content = uploaded_file.getvalue().decode("utf-8", errors="replace")
        return parse_urls_from_text_block(content)

    return []


def _render_stats(title: str, stats) -> None:
    st.markdown(f"### {title}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Détectées", stats.total_detected)
    col2.metric("Valides", len(stats.valid_urls))
    col3.metric("Uniques", len(stats.unique_urls))
    col4.metric("Invalides", len(stats.invalid_urls))


def main() -> None:
    st.set_page_config(page_title="url-s_to_markdown", layout="wide")
    st.title("url-s_to_markdown — Interface web locale")
    st.write("Lance un traitement URL -> markdown/PDF depuis le navigateur, en réutilisant le pipeline existant.")

    with st.form("run_form"):
        mode = st.radio(
            "Mode d'entrée",
            options=["URL unique", "Liste collée", "Fichier uploadé"],
            horizontal=True,
        )

        single_url = ""
        pasted_urls = ""
        uploaded_file = None

        if mode == "URL unique":
            single_url = st.text_input("URL", placeholder="https://example.com/docs/api")
        elif mode == "Liste collée":
            pasted_urls = st.text_area("Liste d'URLs (une par ligne)", height=180)
        else:
            uploaded_file = st.file_uploader("Fichier texte (.txt)", type=["txt"])

        max_urls = st.number_input("max_urls", min_value=1, value=20, step=1)
        output_root = st.text_input("Dossier de sortie", value="outputs")

        submitted = st.form_submit_button("Lancer le traitement")

    candidates = _get_candidates(mode, single_url, pasted_urls, uploaded_file)
    stats = parse_url_stats_from_candidates(candidates)
    _render_stats("Compteurs avant traitement", stats)

    if not submitted:
        st.info("Renseigne les URLs puis clique sur 'Lancer le traitement'.")
        return

    if not stats.unique_urls:
        st.error("Aucune URL valide fournie. Vérifie ton entrée.")
        return

    try:
        result = run_pipeline(
            stats=stats,
            client=UrllibHTTPClient(),
            output_root=Path(output_root),
            max_urls=int(max_urls),
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Erreur pendant le traitement: {exc}")
        return

    st.success("Traitement terminé.")
    st.markdown("## Résumé final")
    st.write(f"Réussies: **{result.success_count}**")
    st.write(f"Échouées: **{result.failed_count}**")
    st.write(f"Lots créés: **{result.batch_count}**")
    st.write(f"Dossier de sortie: `{result.output_dir}`")

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    st.write(f"Groupes détectés: **{', '.join(manifest.get('groups_detected', [])) or 'Aucun'}**")

    with st.expander("Manifest (JSON)", expanded=False):
        st.json(manifest)

    with st.expander("Plan d'organisation (JSON)", expanded=False):
        plan_json = json.loads(result.organization_plan_json.read_text(encoding="utf-8"))
        st.json(plan_json)

    with st.expander("Plan d'organisation (Markdown)", expanded=False):
        st.code(result.organization_plan_md.read_text(encoding="utf-8"), language="markdown")

    errors_text = result.errors_log_path.read_text(encoding="utf-8")
    with st.expander("Erreurs éventuelles", expanded=False):
        if errors_text.strip():
            st.code(errors_text, language="text")
        else:
            st.write("Aucune erreur.")

    with st.expander("Fichiers générés", expanded=True):
        for file_path in manifest.get("generated_files", []):
            st.write(f"- `{file_path}`")


if __name__ == "__main__":
    main()

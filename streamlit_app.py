"""Interface web Streamlit pour url-s_to_markdown."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from url_s_to_markdown.http_client import UrllibHTTPClient
from url_s_to_markdown.inputs import collect_input_candidates, parse_url_stats_from_candidates, parse_urls_from_text_block
from url_s_to_markdown.pipeline import run_pipeline
from url_s_to_markdown.sitemap import extract_urls_from_sitemap


def _render_stats(title: str, stats) -> None:
    st.markdown(f"### {title}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Détectées", stats.total_detected)
    col2.metric("Valides", len(stats.valid_urls))
    col3.metric("Uniques", len(stats.unique_urls))
    col4.metric("Invalides", len(stats.invalid_urls))


def main() -> None:
    st.set_page_config(page_title="url-s_to_markdown", layout="wide")
    st.markdown(
        """
        <style>
          .stButton>button {background-color:#2563eb;color:white;border-radius:8px;border:0;}
          .stRadio [data-baseweb="radio"] div[aria-checked="true"] {background-color:#dbeafe !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("url-s_to_markdown — Interface web locale")
    st.write("Lance un traitement URL -> markdown/PDF depuis le navigateur, en réutilisant le pipeline existant.")

    mode = st.radio(
        "Mode d'entrée",
        options=["URL unique", "Liste collée", "Fichier uploadé", "Sitemap XML URL"],
        horizontal=True,
        key="input_mode",
    )

    single_url = ""
    pasted_urls = ""
    uploaded_text = ""
    sitemap_url = ""
    sitemap_include_external = False

    if mode == "URL unique":
        single_url = st.text_input("URL", placeholder="https://example.com/docs/api")
    elif mode == "Liste collée":
        pasted_urls = st.text_area("Liste d'URLs (une par ligne)", height=180)
    elif mode == "Fichier uploadé":
        uploaded_file = st.file_uploader("Fichier texte (.txt)", type=["txt"], key="uploaded_txt")
        if uploaded_file is not None:
            uploaded_text = uploaded_file.getvalue().decode("utf-8", errors="replace")
    else:
        sitemap_url = st.text_input("URL du sitemap XML", placeholder="https://docs.example.com/sitemap.xml")
        sitemap_include_external = st.checkbox(
            "Inclure les URLs externes au domaine du sitemap",
            value=False,
        )

    max_urls = st.number_input("max_urls", min_value=1, value=20, step=1)
    output_root = st.text_input("Dossier de sortie", value="outputs")
    include_artifacts = st.checkbox("Mode avancé : conserver les artefacts techniques", value=False)

    client = UrllibHTTPClient()
    input_candidates = collect_input_candidates(
        single_url=single_url,
        urls=parse_urls_from_text_block(pasted_urls) + parse_urls_from_text_block(uploaded_text),
        file_path=None,
    )

    sitemap_result = None
    if mode == "Sitemap XML URL" and sitemap_url.strip():
        sitemap_result = extract_urls_from_sitemap(
            sitemap_url.strip(),
            client,
            same_domain_only=not sitemap_include_external,
        )
        input_candidates.extend(sitemap_result.urls)

    stats = parse_url_stats_from_candidates(input_candidates)
    _render_stats("Compteurs avant traitement", stats)

    if sitemap_result is not None:
        st.markdown("### Détails sitemap")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sitemaps détectés", sitemap_result.sitemaps_detected)
        c2.metric("URLs extraites", len(sitemap_result.urls))
        c3.metric("URLs invalides sitemap", len(sitemap_result.invalid_urls))
        if sitemap_result.errors:
            st.warning("Certaines erreurs sitemap ont été détectées. Elles n'arrêtent pas le traitement.")

    if not st.button("Lancer le traitement", type="primary"):
        st.info("Renseigne les URLs puis clique sur 'Lancer le traitement'.")
        return

    if not stats.unique_urls:
        st.error("Aucune URL valide fournie. Vérifie ton entrée.")
        return

    try:
        result = run_pipeline(
            stats=stats,
            client=client,
            output_root=Path(output_root),
            max_urls=int(max_urls),
            include_artifacts=include_artifacts,
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

    livrables = [str(path) for path in result.generated_files if path.suffix in {".md", ".pdf"}]
    st.markdown("### Livrables (.md / .pdf)")
    for file_path in livrables:
        st.write(f"- `{file_path}`")

    if include_artifacts:
        if result.manifest_path and result.manifest_path.exists():
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            st.write(f"Groupes détectés: **{', '.join(manifest.get('groups_detected', [])) or 'Aucun'}**")
            with st.expander("Manifest (JSON)", expanded=False):
                st.json(manifest)

        if result.organization_plan_json and result.organization_plan_json.exists():
            with st.expander("Plan d'organisation (JSON)", expanded=False):
                plan_json = json.loads(result.organization_plan_json.read_text(encoding="utf-8"))
                st.json(plan_json)

        if result.organization_plan_md and result.organization_plan_md.exists():
            with st.expander("Plan d'organisation (Markdown)", expanded=False):
                st.code(result.organization_plan_md.read_text(encoding="utf-8"), language="markdown")

        with st.expander("Erreurs éventuelles", expanded=False):
            if sitemap_result and sitemap_result.errors:
                st.code("\n".join(sitemap_result.errors), language="text")
            if result.errors_log_path and result.errors_log_path.exists():
                errors_text = result.errors_log_path.read_text(encoding="utf-8")
                if errors_text.strip():
                    st.code(errors_text, language="text")


if __name__ == "__main__":
    main()

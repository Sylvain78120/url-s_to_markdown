"""Point d'entrée CLI du MVP."""

from __future__ import annotations

import argparse
from pathlib import Path

from .http_client import UrllibHTTPClient
from .inputs import collect_input_candidates, parse_url_stats_from_candidates
from .pipeline import run_pipeline
from .sitemap import extract_urls_from_sitemap

DEFAULT_MAX_URLS = 20


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="url2md",
        description="Convertit des URLs en markdown et PDF minimal.",
    )
    parser.add_argument("--url", help="URL unique")
    parser.add_argument("--urls", nargs="+", help="Liste d'URLs")
    parser.add_argument("--file", dest="file_path", help="Fichier texte contenant une URL par ligne")
    parser.add_argument("--sitemap-url", help="URL d'un sitemap XML distant")
    parser.add_argument(
        "--sitemap-include-external",
        action="store_true",
        help="Inclure aussi les URLs hors domaine du sitemap (défaut: non)",
    )
    parser.add_argument(
        "--output-root",
        default="outputs",
        help="Dossier racine de sortie (défaut: outputs)",
    )
    parser.add_argument(
        "--max-urls",
        type=int,
        default=DEFAULT_MAX_URLS,
        help=f"Nombre maximum d'URLs uniques par lot (défaut: {DEFAULT_MAX_URLS})",
    )
    parser.add_argument(
        "--include-artifacts",
        action="store_true",
        help="Conserver aussi les artefacts techniques (manifest, plan, logs, pages).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = UrllibHTTPClient()

    input_candidates = collect_input_candidates(single_url=args.url, urls=args.urls, file_path=args.file_path)

    sitemap_result = None
    if args.sitemap_url:
        sitemap_result = extract_urls_from_sitemap(
            args.sitemap_url,
            client,
            same_domain_only=not args.sitemap_include_external,
        )
        input_candidates.extend(sitemap_result.urls)

    stats = parse_url_stats_from_candidates(input_candidates)

    print("=== Compteur URLs (avant traitement) ===")
    print(f"Total détectées: {stats.total_detected}")
    print(f"Valides: {len(stats.valid_urls)}")
    print(f"Uniques: {len(stats.unique_urls)}")
    print(f"Invalides: {len(stats.invalid_urls)}")

    if sitemap_result is not None:
        print("--- Détails sitemap ---")
        print(f"Sitemaps détectés: {sitemap_result.sitemaps_detected}")
        print(f"URLs extraites: {len(sitemap_result.urls)}")
        print(f"URLs invalides dans sitemap: {len(sitemap_result.invalid_urls)}")
        if sitemap_result.errors:
            print(f"Erreurs sitemap: {len(sitemap_result.errors)}")

    if not stats.unique_urls:
        print("Erreur: aucune URL valide fournie (utilise --url, --urls, --file ou --sitemap-url).")
        return 1

    result = run_pipeline(
        stats=stats,
        client=client,
        output_root=Path(args.output_root),
        max_urls=args.max_urls,
        include_artifacts=args.include_artifacts,
    )

    print("\n=== Résumé final ===")
    print(f"Total détectées: {stats.total_detected}")
    print(f"Valides: {len(stats.valid_urls)}")
    print(f"Uniques: {len(stats.unique_urls)}")
    print(f"Invalides: {result.invalid_count}")
    print(f"Échouées: {result.failed_count}")
    print(f"Réussies: {result.success_count}")
    print(f"Lots créés: {result.batch_count}")
    print(f"Dossier de sortie: {result.output_dir}")
    if result.organization_plan_json:
        print(f"Plan JSON: {result.organization_plan_json}")
    if result.organization_plan_md:
        print(f"Plan MD: {result.organization_plan_md}")
    if result.manifest_path:
        print(f"Manifest: {result.manifest_path}")
    if result.errors_log_path:
        print(f"Log erreurs: {result.errors_log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

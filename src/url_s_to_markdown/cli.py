"""Point d'entrée CLI du MVP."""

from __future__ import annotations

import argparse
from pathlib import Path

from .http_client import UrllibHTTPClient
from .inputs import parse_url_stats
from .pipeline import run_pipeline

DEFAULT_MAX_URLS = 20


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="url2md",
        description="Convertit des URLs en markdown et PDF minimal.",
    )
    parser.add_argument("--url", help="URL unique")
    parser.add_argument("--urls", nargs="+", help="Liste d'URLs")
    parser.add_argument("--file", dest="file_path", help="Fichier texte contenant une URL par ligne")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    stats = parse_url_stats(single_url=args.url, urls=args.urls, file_path=args.file_path)
    print("=== Compteur URLs (avant traitement) ===")
    print(f"Total détectées: {stats.total_detected}")
    print(f"Valides: {len(stats.valid_urls)}")
    print(f"Uniques: {len(stats.unique_urls)}")
    print(f"Invalides: {len(stats.invalid_urls)}")

    if not stats.unique_urls:
        print("Erreur: aucune URL valide fournie (utilise --url, --urls ou --file).")
        return 1

    result = run_pipeline(
        stats=stats,
        client=UrllibHTTPClient(),
        output_root=Path(args.output_root),
        max_urls=args.max_urls,
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
    print(f"Plan JSON: {result.organization_plan_json}")
    print(f"Plan MD: {result.organization_plan_md}")
    print(f"Manifest: {result.manifest_path}")
    print(f"Log erreurs: {result.errors_log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

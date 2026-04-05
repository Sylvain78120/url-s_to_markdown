# url-s_to_markdown

Outil Python local pour convertir des URLs en fichiers markdown et PDF, avec organisation automatique, manifeste et logs.

## Installation

Depuis la racine du projet :

```bash
python -m pip install -e .
```

## Lancer l'interface web (Streamlit)

Commande exacte :

```bash
streamlit run streamlit_app.py
```

Ensuite ouvre ton navigateur sur :

- `http://localhost:8501`

## Interface web : ce que tu peux faire

- choisir un mode d'entrée : URL unique, liste collée, fichier `.txt`,
- régler `max_urls` et le dossier de sortie,
- lancer le traitement via un bouton,
- voir les compteurs avant traitement,
- voir le résumé final (réussies, échouées, lots, groupes, dossier),
- consulter manifeste, plan d'organisation, erreurs et fichiers générés.

## Continuer à utiliser la CLI

La CLI est toujours disponible :

```bash
url2md --file urls.txt --max-urls 10
```

## Différence CLI vs Navigateur

- **CLI** : rapide pour scripts/terminal/automatisation.
- **Streamlit** : plus simple pour un débutant qui préfère une interface visuelle.

Les deux utilisent le **même pipeline Python**.

## Utilisation CLI (rappel)

```bash
url2md --url https://example.com
url2md --urls https://example.com/docs/api/a https://example.com/blog/post
url2md --file urls.txt --max-urls 10 --output-root ./mes_sorties
```

## Structure de sortie

```text
outputs/
  <YYYYMMDD_Run_HHMMSS>/
    organization_plan.json
    organization_plan.md
    manifest.json
    logs/
      errors.log
    groups/
      <YYYYMMDD_Title>/
        <YYYYMMDD_Title>.md
        <YYYYMMDD_Title>.pdf
        pages/
          <YYYYMMDD_Title>.md
```

## Tests

```bash
python -m pytest -q
```

## Notes

- Regroupement logique par arborescence URL : `docs/<segment>`, `blog`, sinon domaine + 1er segment.
- Convention de nommage des fichiers principaux : `YYYYMMDD_Title`.
- PDF générés volontairement minimalistes (texte simple) pour rester déterministe.

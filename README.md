# url-s_to_markdown

Outil Python local pour convertir des URLs en fichiers markdown et PDF, avec organisation automatique et support sitemap XML.

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

- choisir un mode d'entrée : URL unique, liste collée, fichier `.txt`, **Sitemap XML URL**,
- régler `max_urls` et le dossier de sortie,
- lancer le traitement via un bouton,
- voir les compteurs avant traitement,
- voir le résumé final (réussies, échouées, lots, groupes, dossier).

### Mode Sitemap XML (web)

- Mode : **Sitemap XML URL**
- Saisir une URL de sitemap (ex: `https://docs.lovable.dev/sitemap.xml`)
- Option : inclure ou non les URLs externes au domaine du sitemap
- Par défaut, l'app **garde seulement le même domaine** (comportement prudent).

## Sortie par défaut (simple)

Par défaut, l'outil produit et affiche uniquement les livrables utiles :

- fichiers `.md`
- fichiers `.pdf`

Les artefacts techniques (manifest, plan, logs, pages intermédiaires) sont désactivés par défaut.

### Activer les artefacts techniques (mode avancé)

CLI :

```bash
url2md --file urls.txt --include-artifacts
```

Streamlit :

- cocher **"Mode avancé : conserver les artefacts techniques"**.


## Mode "documentation site"

CLI :

```bash
url2md --url https://docs.example.com/docs --documentation-mode auto
```

Options utiles :
- `--documentation-mode off|auto|force`
- `--doc-max-pages`
- `--doc-max-depth`

Le mode documentation :
- détecte des signaux documentaires combinés (URL + structure HTML),
- limite le crawl au périmètre documentaire interne,
- exclut les pages non documentaires courantes (blog/pricing/legal/login),
- classe les pages en sections (API, Features, FAQ, etc.),
- génère un `index.md` et des sections avec pages + agrégats.

## Continuer à utiliser la CLI

Exemple simple :

```bash
url2md --file urls.txt --max-urls 10
```

Exemple sitemap en CLI :

```bash
url2md --sitemap-url https://docs.lovable.dev/sitemap.xml
```

Pour inclure aussi les URLs externes au domaine du sitemap :

```bash
url2md --sitemap-url https://docs.lovable.dev/sitemap.xml --sitemap-include-external
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

## Tests

```bash
python -m pytest -q
```

## Notes / limites

- Sitemaps supportés : `urlset` et `sitemapindex` (avec profondeur max simple).
- Sur `sitemapindex`, si un sous-sitemap échoue, le traitement continue avec les autres.
- L'extraction filtre certains éléments bruyants courants (nav/header/footer/cookies), avec heuristique simple.
- Les fichiers agrégés annoncent explicitement leur périmètre (type, source racine, date, nombre de pages, URLs incluses) et séparent clairement chaque page.
- PDF générés volontairement minimalistes (texte simple) pour rester déterministe.

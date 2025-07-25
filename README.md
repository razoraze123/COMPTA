# 🧾 PyCompta – Application de Comptabilité Personnalisée avec PySide6

**PyCompta** est une application de comptabilité à double entrée, 100 % personnalisable, conçue avec **PySide6**. Elle intègre progressivement des modules métiers (comptabilité, scraping, visualisation, export, etc.) autour d'une interface moderne inspirée d'outils professionnels comme Odoo.

---

## 🚀 Objectifs du projet

- 📊 **Gérer une comptabilité à partie double** (journal, bilan, compte de résultat…)
- 🧩 **Décomposer en modules** facilement personnalisables
- 🖥️ **Construire une interface visuelle claire, modulaire et moderne**
- 🔍 **Intégrer un module de scraping** pour automatiser des traitements de données
- 📁 **Préparer les exports PDF, Excel, CSV des écritures**
- 🧮 **Afficher la balance générale dynamique via l'onglet Révision**

---

## 📐 Structure du projet

```bash
PyCompta/
├── main.py                  # Point d'entrée de l'application
├── ui/                      # Interface utilisateur (PySide6)
│   ├── main_window.py       # Fenêtre principale avec sidebar et widgets
│   ├── sidebar.py           # Menu vertical à gauche
│   └── onglets/             # Pages et modules par section
│       ├── onglet_compta.py
│       ├── onglet_scraping.py
│       └── onglet_config.py
├── ressources/              # Icônes, thèmes, fichiers statiques
│   └── style.qss
└── README.md

🧱 Technologies utilisées
🐍 Python 3.10+

💠 PySide6

📁 SQLite (ou système de fichiers .json/.csv selon les modules)

🧪 pytest (pour les futurs tests unitaires)

💅 Thème sombre/clair en QSS

# Cloner le dépôt
git clone https://github.com/votre-utilisateur/PyCompta.git
cd PyCompta

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # (ou venv\Scripts\activate sous Windows)

# Installer les dépendances
pip install -r requirements.txt
If running `python main.py` shows 'No module named PySide6', make sure you executed `pip install -r requirements.txt`.

# Lancer l'application
python main.py

Lorsque vous ajoutez des comptes ou des profils depuis les pages
"Comptes" ou "Profil Scraping", les autres onglets se mettent à jour
immédiatement grâce aux signaux. Les profils sont reliés à la page
"Scraping Images" par le signal `profiles_updated` ; il n'est donc plus
nécessaire de relancer l'application pour voir les nouveaux profils.
Modules prévus (roadmap)
 Interface de base avec sidebar

 Module de saisie comptable (journal, écritures, plan comptable)

  Ajout des onglets "Achat", "Ventes" et "Comptes" dans la section Comptabilité

 Génération automatique du bilan et du compte de résultat

 Système de sauvegarde et export CSV/Excel/PDF

Module de scraping (images, descriptions, variantes…)

Tableau de bord avec indicateurs personnalisés

Interface configuration (chemins, utilisateurs, préférences)

## Configuration du driver Selenium

Pour pouvoir lancer un navigateur contrôlé par **Selenium**, vous devez
installer **Chrome**. L'utilitaire `chromedriver` est récupéré
automatiquement via **webdriver‑manager** s'il n'est pas présent dans votre
`PATH`. En environnement restreint, vous pouvez toujours fournir un chemin
manuel : l'appel à `setup_driver` lèvera sinon
`FileNotFoundError`.

La fonction `setup_driver` utilisée par le module de scraping accepte désormais
trois paramètres optionnels :

- `window_size` : tuple `(largeur, hauteur)` pour définir la taille de la
  fenêtre Chrome (par défaut `1920, 1080`).
- `timeout` : durée maximale de chargement des pages en secondes. Laisser
  `None` pour reproduire le comportement actuel sans limite.
- `chromedriver_path` : chemin explicite vers l'exécutable `chromedriver` pour
  ignorer la détection automatique.

```python
from MOTEUR.scraping.image_scraper.driver import setup_driver

# Exemple avec taille de fenêtre personnalisée ; chromedriver sera téléchargé si
# nécessaire
driver = setup_driver(window_size=(1280, 720), timeout=30)

# Ou en précisant un chemin spécifique au chromedriver
driver = setup_driver(chromedriver_path="/usr/local/bin/chromedriver")
```

## Widget de scraping combiné

Le `CombinedScrapeWidget` lance en une seule étape :

1. le téléchargement des images du concurrent ;
2. la création des liens WooCommerce depuis le dossier local ;
3. la récupération des variantes du produit.

Une fois l'opération terminée, un tableau rassemble les informations suivantes :

| Variante | Lien Woo |
|----------|----------|
| Red | https://shop.com/wp-content/uploads/2024/05/a.jpg |
| Blue | https://shop.com/wp-content/uploads/2024/05/b.png |
|  | https://shop.com/wp-content/uploads/2024/05/c.png |

Les liens WooCommerce sont appariés aux variantes en cherchant un mot clé
dans le nom du fichier d'image. Par exemple, le fichier `camel.webp` sera
automatiquement associé à la variante « Camel ».

Un bouton « Exporter CSV » permet d'enregistrer les couples Variante/Lien Woo
dans un fichier pour une utilisation ultérieure.

## 🧪 Lancer les tests

Après avoir installé les dépendances du projet avec :

```bash
pip install -r requirements.txt
```

les tests unitaires peuvent ensuite être exécutés avec **pytest** depuis la racine du dépôt :

```bash
PYTHONPATH=. pytest

```

### Vérification du style

Le dépôt inclut une configuration **flake8** (`.flake8`) fixant notamment la
longueur maximale des lignes à 100 caractères. Vous pouvez vérifier le code
avec :

```bash
flake8
```

### Commande combinée

Une cible `make check` est fournie pour lancer à la fois **flake8** et les tests :

```bash
make check
```

## 📤 Export FEC et TVA

Un script de migration minimal est fourni. Avant la première exécution :

```bash
python migrations.py
```

Pour charger quelques données de démonstration :

```bash
python sample_data.py
```

Le fichier des écritures comptables peut ensuite être généré pour une année :

```bash
python - <<'PY'
from pathlib import Path
from MOTEUR.compta.accounting.db import export_fec
export_fec('demo.db', 2024, Path('fec.csv'))
PY
```

La fonction `get_vat_summary` de `achat_db` permet d'obtenir le récapitulatif de TVA par taux pour l'établissement de la CA3.

🔧 Contribution
Ce projet est en développement actif. Toute idée, retour ou contribution est bienvenue.
Deux fichiers texte servent de référence pour le code :
- `MOTEUR/compta/compta.txt`
- `MOTEUR/scraping/scraping.txt`
Ils doivent être mis à jour à chaque ajout ou modification de code afin de rester cohérents avec les modules correspondants.

🧠 Auteur
Projet conçu et maintenu par Lamine.

📄 Licence
Ce projet est open-source sous licence MIT.

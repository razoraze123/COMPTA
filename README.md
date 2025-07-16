# 🧾 PyCompta – Application de Comptabilité Personnalisée avec PySide6

**PyCompta** est une application de comptabilité à double entrée, 100 % personnalisable, conçue avec **PySide6**. Elle intègre progressivement des modules métiers (comptabilité, scraping, visualisation, export, etc.) autour d'une interface moderne inspirée d'outils professionnels comme Odoo.

---

## 🚀 Objectifs du projet

- 📊 **Gérer une comptabilité à partie double** (journal, bilan, compte de résultat…)
- 🧩 **Décomposer en modules** facilement personnalisables
- 🖥️ **Construire une interface visuelle claire, modulaire et moderne**
- 🔍 **Intégrer un module de scraping** pour automatiser des traitements de données
- 📁 **Préparer les exports PDF, Excel, CSV des écritures**

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

# Lancer l'application
python main.py
Modules prévus (roadmap)
 Interface de base avec sidebar

 Module de saisie comptable (journal, écritures, plan comptable)

 Génération automatique du bilan et du compte de résultat

 Système de sauvegarde et export CSV/Excel/PDF

 Module de scraping (images, descriptions, variantes…)

 Tableau de bord avec indicateurs personnalisés

 Interface configuration (chemins, utilisateurs, préférences)
🔧 Contribution
Ce projet est en développement actif. Toute idée, retour ou contribution est bienvenue.

🧠 Auteur
Projet conçu et maintenu par Lamine.

📄 Licence
Ce projet est open-source sous licence MIT.

# PythonProject1

Ce projet est une application Python pour la gestion et la synchronisation de données liées à des sessions utilisateur, des groupes, des sujets, des comptes, et plus encore. Il utilise MariaDB comme base de données et propose des scripts pour insérer, mettre à jour et traiter différentes entités.

## Structure du projet

- `main_system.py` : Script principal du système.
- `push_data/` : Dossier contenant les scripts de gestion des données (utilisateurs, sessions, groupes, etc.).
- `download_images/` : Dossier pour la gestion et le téléchargement d'images.
- `config.json` : Fichier de configuration du projet.
- `sync_status.json` : Fichier de suivi de la synchronisation.

## Installation

1. Clonez le dépôt ou copiez les fichiers dans votre environnement local.
2. Installez les dépendances nécessaires (ex : `mysql-connector-python`).
   ```bash
   pip install mysql-connector-python
   ```
3. Configurez la base de données MariaDB et mettez à jour `config.json` si besoin.

## Utilisation

- Lancez le script principal :
  ```bash
  python main_system.py
  ```
- Les scripts du dossier `push_data/` peuvent être utilisés pour insérer ou mettre à jour les données dans la base.

## Scripts principaux

- `handle_relationUserSession_data.py` : Gère l'insertion et la mise à jour des relations utilisateur-session.
- `handle_account_data.py` : Gère les comptes utilisateurs.
- `handle_session_data.py` : Gère les sessions.
- ...

## Configuration

Adaptez le fichier `config.json` pour renseigner les paramètres de connexion à la base de données et autres options spécifiques.

## Contribution

Les contributions sont les bienvenues ! Veuillez ouvrir une issue ou une pull request pour proposer des améliorations.

## Licence

Ce projet est sous licence MIT.


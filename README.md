# API Ndock

## Aperçu du Projet

Ndock est une API RESTful développée avec FastAPI pour gérer un système de commande de nourriture en ligne. L'API permet aux utilisateurs de s'inscrire, de parcourir les restaurants, de consulter les menus, de passer des commandes et de suivre les livraisons.

## Table des Matières

- [Fonctionnalités](#fonctionnalités)
- [Structure du Projet](#structure-du-projet)
- [Installation](#installation)
- [Configuration](#configuration)
- [Base de Données](#base-de-données)
- [Authentification](#authentification)
- [API Endpoints](#api-endpoints)
- [Déploiement](#déploiement)
- [Exemples d'Utilisation](#exemples-dutilisation)

## Fonctionnalités

- **Gestion des Utilisateurs**: Inscription, connexion et gestion des profils utilisateurs
- **Gestion des Restaurants**: Ajout, modification et suppression de restaurants
- **Gestion des Menus**: Création et gestion des menus avec catégories et suppléments
- **Système de Commande**: Création et suivi des commandes
- **Gestion des Livraisons**: Suivi des livraisons de commandes
- **Système de Commentaires**: Évaluation et commentaires sur les menus

## Structure du Projet

```
api/
├── alembic.ini                  # Configuration Alembic pour les migrations
├── api.json                     # Documentation API
├── config/                      # Configuration de l'application
├── db/                          # Modèles et schémas de base de données
├── dependencies/                # Dépendances FastAPI
├── docs/                        # Documentation supplémentaire
├── main.py                      # Point d'entrée de l'application
├── middleware/                  # Middleware FastAPI
├── migrations/                  # Migrations de base de données
├── render.yaml                  # Configuration de déploiement Render
├── requirements.txt             # Dépendances Python
├── routes/                      # Routes API
├── services/                    # Services métier
├── tests/                       # Fichiers de test HTTP
└── utils/                       # Utilitaires
```

## Installation

### Prérequis

- Python 3.8+
- PostgreSQL

### Étapes d'Installation

1. Cloner le dépôt:
   ```bash
   git clone <url-du-dépôt>
   cd ndock/api
   ```

2. Créer un environnement virtuel:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
   ```

3. Installer les dépendances:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurer les variables d'environnement (ou créer un fichier `.env`):
   ```
   DATABASE_URL=postgresql://utilisateur:mot_de_passe@localhost:5432/ndock
   SECRET_KEY=votre_clé_secrète
   ```

5. Appliquer les migrations:
   ```bash
   alembic upgrade head
   ```

6. Lancer l'application:
   ```bash
   uvicorn main:app --reload
   ```

## Configuration

La configuration de l'application est gérée dans `config/settings.py`. Les paramètres principaux incluent:

- **DATABASE_URL**: URL de connexion à la base de données PostgreSQL
- **SECRET_KEY**: Clé secrète pour la génération des tokens JWT
- **ACCESS_TOKEN_EXPIRE_MINUTES**: Durée de validité des tokens d'accès
- **CORS_ORIGINS**: Liste des origines autorisées pour les requêtes CORS

Ces paramètres peuvent être configurés via des variables d'environnement ou un fichier `.env`.

## Base de Données

### Modèles Principaux

- **User**: Utilisateurs du système
- **Restaurant**: Restaurants disponibles sur la plateforme
- **MenuCategory**: Catégories de menus
- **Menu**: Éléments de menu proposés par les restaurants
- **Supplement**: Suppléments pouvant être ajoutés aux menus
- **Order**: Commandes passées par les utilisateurs
- **OrderItem**: Éléments individuels dans une commande
- **Shipment**: Informations de livraison pour les commandes
- **Comment**: Commentaires et évaluations sur les menus

### Migrations

Les migrations de base de données sont gérées avec Alembic. Pour créer une nouvelle migration:

```bash
alembic revision --autogenerate -m "description_de_la_migration"
```

Pour appliquer les migrations:

```bash
alembic upgrade head
```

## Authentification

L'API utilise l'authentification JWT (JSON Web Tokens):

1. L'utilisateur s'inscrit via `/auth/register` ou se connecte via `/auth/login`
2. L'API renvoie un token d'accès JWT
3. Ce token doit être inclus dans l'en-tête `Authorization` des requêtes ultérieures

Exemple d'en-tête d'autorisation:
```
Authorization: Bearer <token>
```

## API Endpoints

### Authentification
- `POST /auth/register` - Inscription d'un nouvel utilisateur
- `POST /auth/login` - Connexion utilisateur
- `GET /auth/me` - Obtenir les informations de l'utilisateur actuel

### Restaurants
- `POST /restaurants` - Créer un nouveau restaurant
- `GET /restaurants` - Lister tous les restaurants
- `GET /restaurants/{restaurant_id}` - Obtenir un restaurant spécifique
- `PUT /restaurants/{restaurant_id}` - Mettre à jour un restaurant
- `DELETE /restaurants/{restaurant_id}` - Supprimer un restaurant

### Menus
- `POST /restaurants/{restaurant_id}/menus` - Ajouter un menu à un restaurant
- `GET /restaurants/{restaurant_id}/menus` - Lister les menus d'un restaurant
- `GET /menus/{menu_id}` - Obtenir un menu spécifique
- `PUT /menus/{menu_id}` - Mettre à jour un menu
- `DELETE /menus/{menu_id}` - Supprimer un menu

### Catégories de Menu
- `POST /menu-categories` - Créer une nouvelle catégorie
- `GET /menu-categories` - Lister toutes les catégories
- `GET /menu-categories/{category_id}` - Obtenir une catégorie spécifique
- `PUT /menu-categories/{category_id}` - Mettre à jour une catégorie
- `DELETE /menu-categories/{category_id}` - Supprimer une catégorie

### Suppléments
- `POST /supplements` - Créer un nouveau supplément
- `GET /supplements` - Lister tous les suppléments
- `GET /supplements/{supplement_id}` - Obtenir un supplément spécifique
- `PUT /supplements/{supplement_id}` - Mettre à jour un supplément
- `DELETE /supplements/{supplement_id}` - Supprimer un supplément

### Commandes
- `POST /orders` - Créer une nouvelle commande
- `GET /orders/{order_id}` - Obtenir une commande spécifique
- `GET /users/{user_id}/orders` - Lister les commandes d'un utilisateur
- `GET /restaurants/{restaurant_id}/orders` - Lister les commandes d'un restaurant

### Commentaires
- `POST /menus/{menu_id}/comments` - Ajouter un commentaire à un menu
- `GET /menus/{menu_id}/comments` - Lister les commentaires d'un menu

### Livraisons
- `POST /orders/{order_id}/shipments` - Créer une livraison pour une commande
- `GET /shipments/{shipment_id}` - Obtenir une livraison spécifique
- `PUT /shipments/{shipment_id}` - Mettre à jour le statut d'une livraison

## Déploiement

L'application est configurée pour être déployée sur Render, une plateforme cloud. La configuration se trouve dans le fichier `render.yaml`.

Pour déployer l'application:

1. Créez un compte sur [Render](https://render.com/)
2. Connectez votre dépôt GitHub
3. Configurez les variables d'environnement nécessaires
4. Déployez l'application

## Exemples d'Utilisation

### Inscription d'un Utilisateur

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com",
    "password": "mot_de_passe_sécurisé",
    "phone_number": "+33612345678",
    "address": "123 Rue de Paris, 75001 Paris"
  }'
```

### Création d'une Commande

```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <votre_token>" \
  -d '{
    "client_id": 1,
    "items": [
      {
        "menu_id": 1,
        "quantity": 2,
        "supplements": [
          {
            "supplement_id": 3,
            "quantity": 1
          }
        ]
      }
    ]
  }'
```

### Obtention des Menus d'un Restaurant

```bash
curl -X GET "http://localhost:8000/restaurants/1/menus" \
  -H "Authorization: Bearer <votre_token>"
```
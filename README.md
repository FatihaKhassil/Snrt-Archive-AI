# SNRT Smart Archive AI

## Présentation

**SNRT Smart Archive AI** est une plateforme de gestion et d’exploitation intelligente des archives de la SNRT. Elle centralise les documents et les contenus audio, automatise leur traitement et rend leur contenu accessible par recherche textuelle, recherche sémantique et questions formulées en langage naturel.

L’objectif est de transformer un fonds d’archives hétérogène en une source d’information consultable, enrichie et traçable. L’interface propose notamment le dépôt de fichiers, la consultation des archives, un tableau de bord, la gestion des utilisateurs et des espaces de recherche dédiés.

## Fonctionnalités

- Import et stockage de documents et de fichiers audio ;
- Extraction du texte des documents avec Apache Tika ;
- Transcription des contenus audio avec Whisper ;
- Enrichissement automatique des contenus par un modèle de langage ;
- Indexation pour la recherche par mots-clés avec Apache Solr ;
- Découpage en passages, génération d’embeddings et recherche sémantique avec ChromaDB ;
- Question-réponse contextualisée grâce à un mécanisme RAG (*Retrieval-Augmented Generation*) ;
- Authentification, contrôle des rôles, gestion des utilisateurs et suivi des archives ;
- Observabilité avec métriques, journaux et tableaux de bord.

## Parcours de traitement d’une archive

```text
Dépôt du fichier
       │
       ▼
API FastAPI ──► MongoDB + stockage de fichiers ──► Kafka
                                                      │
               ┌──────────────────────────────────────┴──────────────────────────────────────┐
               ▼                                                                             ▼
      Document : Apache Tika                                                       Audio : Whisper
               └──────────────────────────────────────┬──────────────────────────────────────┘
                                                      ▼
                                            Texte extrait ou transcrit
                                                      │
                                                      ▼
                                          Enrichissement par le LLM
                                               ┌──────┴──────┐
                                               ▼             ▼
                                      Apache Solr        ChromaDB
                                   recherche textuelle  recherche sémantique / RAG
```

Les workers communiquent de manière asynchrone via Apache Kafka. Cette séparation permet de traiter les fichiers sans bloquer l’API et d’isoler chaque étape : traitement documentaire, transcription, enrichissement, indexation vectorielle et indexation textuelle.

## Architecture du projet

| Répertoire / service | Rôle |
|---|---|
| `frontend` | Interface web React construite avec Vite et Material UI. |
| `backend-fastapi` | API REST FastAPI : dépôt, recherche, RAG, documents, authentification, utilisateurs et statistiques. |
| `workers/audio-worker` | Transcription des fichiers audio avec Whisper. |
| `workers/document-worker` | Extraction de texte des documents via Apache Tika. |
| `workers/llm-worker` | Enrichissement du contenu extrait avec le modèle de langage. |
| `workers/embedding-worker` | Découpage du texte, création des embeddings et stockage dans ChromaDB. |
| `workers/solr-worker` | Préparation et indexation des archives dans Apache Solr. |
| `prometheus`, `grafana`, `loki` | Collecte des métriques, visualisation et centralisation des journaux. |
| `storage` | Volume local partagé pour les fichiers déposés. |

## Recherche intelligente

La plateforme met à disposition trois modes complémentaires :

- **Recherche textuelle** : Apache Solr interroge les champs indexés, notamment le titre, le résumé, les mots-clés et la transcription.
- **Recherche sémantique** : les contenus sont découpés en passages et convertis en vecteurs avec `nomic-embed-text`, via Ollama. ChromaDB retrouve les passages les plus proches du sens de la requête.
- **RAG** : les passages pertinents retrouvés servent de contexte à un LLM pour produire une réponse fondée sur les archives disponibles.

Le service de génération de réponses peut être configuré pour utiliser **Groq** ou une exécution locale avec **Ollama**, selon les variables d’environnement. Ollama est également utilisé pour les embeddings ; le worker d’enrichissement s’appuie sur son service local.

## Stack technique

| Besoin | Technologie |
|---|---|
| Frontend | React, Vite, Material UI |
| API | FastAPI |
| Communication asynchrone | Apache Kafka |
| Base de données | MongoDB |
| Extraction documentaire | Apache Tika |
| Transcription audio | OpenAI Whisper |
| Recherche textuelle | Apache Solr |
| Recherche vectorielle | ChromaDB |
| Embeddings | Ollama / `nomic-embed-text` |
| LLM | Groq ou Ollama |
| Métriques | Prometheus |
| Logs | Loki et Grafana Alloy |
| Visualisation | Grafana |
| Conteneurisation | Docker Compose |

## Services accessibles localement

Après le démarrage de la stack, les principaux points d’accès sont les suivants :

| Service | Adresse |
|---|---|
| Application web | `http://localhost:5173` |
| API FastAPI | `http://localhost:8000` |
| Documentation API | `http://localhost:8000/docs` |
| ChromaDB | `http://localhost:8001` |
| Apache Solr | `http://localhost:8983` |
| Kafka UI | `http://localhost:8080` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

## Démarrage rapide

### Prérequis

- Docker et Docker Compose ;
- Un fichier `.env` à la racine, contenant les variables de configuration de l’API, de Kafka et, si Groq est sélectionné, les identifiants du fournisseur LLM ;
- Les modèles Ollama nécessaires doivent être disponibles lorsque l’exécution locale est utilisée, en particulier `nomic-embed-text` pour les embeddings.

### Lancer la plateforme

```bash
docker compose up --build
```

Pour lancer les services en arrière-plan :

```bash
docker compose up --build -d
```

Consultez ensuite l’application sur `http://localhost:5173`. Les fichiers envoyés par l’API sont conservés dans le répertoire local `storage`, partagé avec les workers.

## Supervision

Prometheus collecte les métriques exposées par l’API et les workers, notamment les volumes reçus et traités, les erreurs ainsi que les durées de traitement. Grafana fournit les tableaux de bord et l’alerting ; Loki centralise les journaux collectés par Grafana Alloy.

## Guide d’utilisation

### 1. Préparer la configuration

1. Créez ou complétez le fichier `.env` à la racine du projet. Les variables attendues sont :

   ```dotenv
   MONGO_HOST=
   MONGO_PORT=
   MONGO_DB=
   APP_NAME=
   APP_VERSION=
   KAFKA_BOOTSTRAP_SERVERS=
   KAFKA_DOCUMENT_TOPIC=
   KAFKA_TRANSCRIPTION_TOPIC=
   KAFKA_LLM_TOPIC=
   LLM_PROVIDER=
   OLLAMA_BASE_URL=
   OLLAMA_MODEL=
   GROQ_API_KEY=
   GROQ_MODEL=
   GRAFANA_SMTP_USER=
   GRAFANA_SMTP_PASSWORD=
   GRAFANA_SMTP_FROM=
   ```

2. Choisissez le fournisseur de réponses RAG : `LLM_PROVIDER=groq` avec une clé `GROQ_API_KEY`, ou `LLM_PROVIDER=ollama` pour une exécution locale. Ne versionnez jamais les clés ou mots de passe contenus dans `.env`.

3. Démarrez l’ensemble des services :

   ```bash
   docker compose up --build -d
   docker compose ps
   ```

   Attendez que Kafka soit sain et que les conteneurs soient démarrés avant d’importer des archives. La première construction du worker audio peut prendre plus longtemps car Whisper et ses dépendances sont installés.

### 2. Initialiser les modèles Ollama

Ollama est utilisé pour générer les vecteurs de recherche et, selon la configuration, pour l’enrichissement et les réponses. Téléchargez au minimum le modèle d’embedding après le démarrage :

```bash
docker compose exec ollama ollama pull nomic-embed-text
```

Si `LLM_PROVIDER=ollama`, téléchargez également le modèle défini dans `OLLAMA_MODEL` :

```bash
docker compose exec ollama ollama pull <nom-du-modele>
```

Vérifiez les modèles présents avec :

```bash
docker compose exec ollama ollama list
```

### 3. Créer le premier compte administrateur

L’écran de connexion ne permet pas de créer un compte. De plus, les routes de gestion des utilisateurs sont réservées aux administrateurs : sur une installation neuve, le premier compte `ADMIN` doit donc être créé une seule fois dans MongoDB.

> Cette procédure concerne uniquement une base MongoDB vide. Utilisez un mot de passe initial fort et remplacez les valeurs d’exemple par les informations de votre administrateur.

1. Générez un hash bcrypt du mot de passe. Ne stockez jamais un mot de passe en clair dans MongoDB :

   ```bash
   docker compose exec backend python -c "from app.security.password import hash_password; print(hash_password('ChangezMoi!2026'))"
   ```

2. Ouvrez le shell MongoDB :

   ```bash
   docker compose exec mongodb mongosh
   ```

3. Sélectionnez la base dont le nom est défini par `MONGO_DB` dans `.env`, puis insérez le compte et initialisez le compteur. Remplacez `NOM_DE_LA_BASE`, les données personnelles et `COLLER_ICI_LE_HASH_BCRYPT` :

   ```javascript
   use NOM_DE_LA_BASE

   db.counters.updateOne(
     { _id: "users" },
     { $set: { sequence: 1 } },
     { upsert: true }
   )

   db.users.insertOne({
     user_id: "USR-000001",
     first_name: "Prenom",
     last_name: "Nom",
     email: "admin@snrt.ma",
     phone: "0600000000",
     department: "Administration",
     role: "ADMIN",
     status: "ACTIVE",
     password: "COLLER_ICI_LE_HASH_BCRYPT",
     created_at: new Date().toISOString(),
     updated_at: new Date().toISOString()
   })
   ```

4. Quittez avec `exit`, puis connectez-vous sur `http://localhost:5173` avec l’adresse e-mail et le mot de passe choisis à l’étape 1.

Une fois ce premier administrateur créé, tous les comptes suivants doivent être créés depuis l’interface d’administration ; il n’est plus nécessaire de les insérer directement dans MongoDB.

### 4. Vérifier que la plateforme est prête

Ouvrez `http://localhost:5173`, puis utilisez l’interface de connexion. L’API est disponible sur `http://localhost:8000` et sa documentation interactive sur `http://localhost:8000/docs`.

Pour un contrôle rapide côté infrastructure :

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 audio-worker document-worker llm-worker embedding-worker solr-worker
```

Un worker en erreur ou arrêté empêche seulement l’étape associée du pipeline : par exemple, sans `document-worker` les documents ne sont pas extraits ; sans `embedding-worker`, ils restent disponibles en recherche textuelle mais pas en recherche sémantique ni dans le RAG.

### 5. Gérer les utilisateurs et les rôles

Connectez-vous avec un compte `ADMIN`, ouvrez **Utilisateurs**, puis cliquez sur **Ajouter un utilisateur**. Renseignez les informations demandées et choisissez l’un des rôles suivants :

| Rôle | Accès fonctionnel |
|---|---|
| `ADMIN` | Tableau de bord, gestion des utilisateurs, dépôt, consultation des documents et tous les modes de recherche. |
| `DOCUMENTALIST` | Dépôt d’archives, consultation des documents et recherches ; pas de gestion des utilisateurs. |
| `SNRT_USER` | Consultation des documents et recherches ; pas de dépôt ni de gestion des utilisateurs. |

Lors de sa création via l’interface, un utilisateur reçoit actuellement le mot de passe initial **`123456`**. Ce choix est volontairement temporaire : il simplifie les tests de l’application en évitant de gérer plusieurs mots de passe pendant la phase de démonstration et de validation.

> À ce jour, l’interface affiche un lien « Changer le mot de passe », mais l’API de changement de mot de passe n’est pas encore implémentée. Le mot de passe commun `123456` ne doit donc pas être utilisé en production. Avant la mise en production, il faut ajouter un endpoint de changement/réinitialisation de mot de passe et imposer un mot de passe personnel à chaque utilisateur ; en attendant, seul un administrateur technique peut modifier le hash du mot de passe dans MongoDB.

Pour modifier un rôle dans l’interface : **Utilisateurs** → sélectionner l’icône de modification → choisir le rôle dans la liste **Rôle** → **Enregistrer**. Le statut peut également être changé entre `ACTIVE` et `INACTIVE`.

Pour un dépannage exceptionnel directement dans MongoDB, modifiez uniquement le champ `role` avec l’une des valeurs exactes `ADMIN`, `DOCUMENTALIST` ou `SNRT_USER` :

```javascript
use NOM_DE_LA_BASE
db.users.updateOne(
  { email: "utilisateur@snrt.ma" },
  { $set: { role: "DOCUMENTALIST", updated_at: new Date().toISOString() } }
)
```

L’utilisateur doit se déconnecter puis se reconnecter afin d’obtenir un nouveau jeton contenant son rôle mis à jour.

### 6. Déposer et suivre une archive

1. Connectez-vous à l’application.
2. Ouvrez la page **Upload** et sélectionnez un document ou un fichier audio.
3. Une fois le dépôt confirmé, le fichier est stocké et un événement Kafka démarre le traitement.
4. Consultez la page **Documents** ou le tableau de bord pour vérifier l’avancement.
5. Patientez jusqu’à la fin du traitement : extraction ou transcription, enrichissement, indexation Solr et génération des embeddings.

Les traitements se font en arrière-plan. Un fichier peut donc apparaître dans la liste avant que toutes les formes de recherche ne soient disponibles.

### 7. Rechercher et interroger les archives

- Utilisez **Search** pour une recherche par mots-clés : elle convient à un titre, une expression exacte, un nom ou un terme précis.
- Utilisez **Semantic Search** pour rechercher une idée, un thème ou une formulation proche, même si les mêmes mots ne sont pas présents dans l’archive.
- Utilisez la fonction de question-réponse/RAG pour poser une question complète. Le système récupère les passages les plus pertinents, puis construit une réponse contextualisée à partir de ces sources.

Pour de meilleurs résultats, privilégiez des questions précises et vérifiez les archives proposées avec la réponse. La recherche sémantique et le RAG ne remplacent pas la validation éditoriale des documents source.

### 8. Administrer la plateforme

Les utilisateurs disposant du rôle administrateur peuvent accéder au tableau de bord et à la gestion des utilisateurs. Ils peuvent suivre les volumes d’archives, l’état du traitement et organiser les accès à l’application. La suppression d’une archive doit être réalisée depuis l’interface ou l’API afin de maintenir la cohérence avec les index de recherche.

## Superviser le système avec Grafana

### Rôle de chaque composant de supervision

| Composant | Ce qu’il fait | Utilisation pratique |
|---|---|---|
| Prometheus | Interroge périodiquement les métriques des cinq workers. | Vérifier la disponibilité, les compteurs de documents, les erreurs et les latences. |
| Grafana | Affiche les métriques et les logs sous forme de tableaux de bord ; gère les alertes. | Observer le pipeline à une seule adresse et repérer rapidement une anomalie. |
| Loki | Stocke et indexe les journaux des conteneurs. | Retrouver l’erreur exacte associée à un worker ou à un document. |
| Grafana Alloy | Collecte les journaux Docker et les envoie à Loki. | Évite de consulter chaque conteneur séparément pour les investigations courantes. |

Le dashboard fourni dans `grafana/dashboards/snrt-monitoring.json` affiche notamment : documents reçus et traités avec succès, échecs, workers disponibles ou indisponibles, erreurs par service, débit, durée de traitement au 95e percentile et dernières erreurs remontées dans les logs.

### Initialiser Grafana lors d’une nouvelle installation

1. Accédez à `http://localhost:3000` et connectez-vous avec le compte administrateur Grafana configuré lors de la première ouverture.
2. Dans **Connections > Data sources**, ajoutez une source **Prometheus** avec l’URL `http://prometheus:9090`, puis testez et enregistrez la connexion.
3. Ajoutez une source **Loki** avec l’URL `http://loki:3100`, puis testez et enregistrez-la.
4. Dans **Dashboards > New > Import**, importez `grafana/dashboards/snrt-monitoring.json` depuis le dépôt et associez les sources Prometheus et Loki créées aux choix demandés.
5. Ouvrez le dashboard **SNRT Archive AI – Monitoring Dashboard** et choisissez la période à analyser.

> La configuration des sources de données n’est pas versionnée dans le projet. Cette initialisation est donc requise sur une instance Grafana neuve.

### Lire le dashboard et réagir

| Signal observé | Interprétation | Première action |
|---|---|---|
| **Workers Down** | Un worker ne répond plus à Prometheus. | Lancez `docker compose ps`, puis consultez ses logs. |
| **Failed Documents** ou **Worker Errors** en hausse | Une étape du pipeline échoue. | Consultez « Latest Worker Errors » dans Grafana ou les logs du worker concerné. |
| Durée P95 élevée | Les traitements les plus lents deviennent anormalement longs. | Vérifiez la charge, la taille/type des fichiers, Whisper et le LLM. |
| Documents reçus mais non traités | Les messages Kafka ou un worker aval sont bloqués. | Contrôlez Kafka UI, puis l’état des workers dans l’ordre du pipeline. |
| Aucune donnée | Prometheus ne collecte pas les métriques ou la source Grafana est mal configurée. | Vérifiez `http://localhost:9090/targets` et la connexion Prometheus de Grafana. |

Une règle d’alerte est fournie pour détecter un worker indisponible pendant au moins une minute. Les paramètres SMTP utilisés pour recevoir les alertes sont lus depuis les variables `GRAFANA_SMTP_*`. Avant une mise en production, configurez l’adresse destinataire dans `grafana/provisioning/alerting/contact-points.yml` et vérifiez que l’identifiant de la source Prometheus référencé par les règles d’alerte correspond à celui de votre instance Grafana.

### Commandes de diagnostic utiles

```bash
# Voir l’état de tous les conteneurs
docker compose ps

# Suivre les logs d’un worker précis
docker compose logs -f document-worker

# Suivre les logs de toute la chaîne de traitement
docker compose logs -f audio-worker document-worker llm-worker embedding-worker solr-worker

# Consulter les topics et les messages Kafka depuis son interface web
# http://localhost:8080

# Vérifier que Prometheus voit bien les cibles
# http://localhost:9090/targets

# Arrêter la plateforme sans supprimer les données persistantes
docker compose down
```

Les données MongoDB, ChromaDB, Ollama, Prometheus, Grafana et Loki sont conservées dans des volumes Docker nommés. Pour repartir de zéro, la suppression de ces volumes est une opération destructive : ne l’effectuez qu’après avoir sauvegardé les données nécessaires.

---

*Projet réalisé par Fatiha Khassil, étudiante à l’ENSIAS, au sein de la SNRT.*

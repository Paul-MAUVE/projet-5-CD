# Exercice 2 — Monitoring Nginx avec AWS OpenSearch

## 1. Présentation

Cet exercice du parcours Expert DevOps OpenClassrooms consiste à déployer une solution de centralisation, d'analyse et de visualisation des logs HTTP d'un serveur Nginx.

L'infrastructure est provisionnée avec Terraform sur AWS. Les logs sont préparés et transformés en documents JSON à l'aide de scripts Python, puis indexés dans Amazon OpenSearch Service.

Un dashboard personnalisé permet de visualiser :

- La répartition des méthodes HTTP (GET, HEAD, POST, PUT) sous forme de diagramme en donut.
- La quantité cumulée de données envoyées par le serveur HTTP, par tranches de 12 heures.
- Le nombre de requêtes des cinq URL les plus sollicitées, par tranches de 12 heures, sous forme d'histogramme empilé.

Le jeu de données contient **14 496 requêtes HTTP Nginx**.

Pour cet exercice, l'importation a été réalisée avec l'API Bulk d'OpenSearch plutôt qu'avec l'assistant d'importation de l'interface. Cette méthode permet d'automatiser le traitement des données et de reproduire facilement l'importation.

## 2. Architecture

```text
Logs Nginx assainis
        |
        v
Script Python (import_nginx.py)
        |
        v
Fichier NDJSON (Bulk API)
        |
        v
Amazon OpenSearch Service
        |
        v
Index nginx-access
        |
        v
OpenSearch Dashboards
        |
        v
Dashboard Nginx - Monitoring HTTP (version finale)
        |
        +--> Donut : méthodes HTTP
        |
        +--> Histogramme : volume de données / 12h
        |
        +--> Histogramme empilé : Top 5 des URL / 12h
```

## 3. Technologies

- Terraform
- AWS CLI
- Amazon OpenSearch Service
- Moteur Elasticsearch 7.10
- Python 3
- API REST OpenSearch
- API Bulk
- OpenSearch Dashboards
- curl

Infrastructure utilisée :

| Paramètre | Configuration |
|---|---|
| Fournisseur cloud | AWS |
| Région | eu-west-3 (Paris) |
| Domaine OpenSearch | oc-p5-elk |
| Instance | t3.small.search |
| Stockage | 10 Gio |
| Index final | nginx-access |
| Documents indexés | 14 496 |
| Nombre de visualisations | 3 |

## 4. Structure du projet

```text
elk/
├── README.md
├── aws/
│   ├── main.tf
│   ├── variables.tf
│   └── .terraform.lock.hcl
├── ingestion/
│   ├── anonymize_nginx.py
│   └── import_nginx.py
├── opensearch/
│   └── create-index.json
├── samples/
│   └── nginx-access-anonymized.log
└── export.ndjson
```

Les fichiers Terraform State, les mots de passe, les fichiers NDJSON intermédiaires et les logs originaux sont exclus du dépôt Git.

Le fichier `export.ndjson` contient la sauvegarde des objets OpenSearch Dashboards du dashboard final.

## 5. Prérequis

Installer et configurer :

- Terraform
- AWS CLI v2
- Python 3
- curl
- Un compte AWS disposant des permissions nécessaires pour Amazon OpenSearch Service

Configurer un profil AWS :

```bash
aws configure --profile terraform-oc-p5
```

Vérifier l'authentification :

```bash
aws sts get-caller-identity --profile terraform-oc-p5
```

Ne jamais publier les identifiants AWS, les mots de passe ou les fichiers Terraform State.

## 6. Déploiement Terraform

Depuis la racine du dépôt :

```bash
cd elk/aws
```

Configurer le profil AWS :

```bash
export AWS_PROFILE=terraform-oc-p5
```

Définir les variables Terraform :

```bash
export TF_VAR_allowed_ip="VOTRE_IP_PUBLIQUE/32"

read -r -s -p "Mot de passe OpenSearch : " TF_VAR_opensearch_master_password
echo

export TF_VAR_opensearch_master_password
```

Remplacer `VOTRE_IP_PUBLIQUE` par l'adresse IPv4 publique du poste autorisé.

Le mot de passe doit être conservé dans un gestionnaire de mots de passe et ne doit jamais être enregistré dans le dépôt.

Initialiser Terraform :

```bash
terraform init
```

Vérifier la configuration :

```bash
terraform validate
terraform plan
```

Déployer l'infrastructure :

```bash
terraform apply
```

Confirmer avec `yes` après vérification du plan.

Le provisionnement du domaine OpenSearch peut prendre plusieurs minutes.

Afficher les endpoints :

```bash
terraform output
```

Les outputs `elasticsearch` et `kibana` correspondent respectivement au point d'accès OpenSearch et à celui de l'interface OpenSearch Dashboards.

Dans cette configuration, les outputs contiennent des noms d'hôte ou des chemins sans préfixe `https://`. Il faut donc ajouter ce préfixe pour les utiliser comme URL.

## 7. Création de l'index OpenSearch

L'index utilisé pour l'exercice est :

`nginx-access`

Le mapping est défini dans :

```text
elk/opensearch/create-index.json
```

Il configure notamment :

- `@timestamp` : date et heure des requêtes.
- `client_ip` : adresse IP du client.
- `method` : méthode HTTP.
- `url` : chemin demandé.
- `http_version` : version du protocole HTTP.
- `status` : code de réponse HTTP.
- `bytes` : volume de données envoyées.
- `referer` : référent HTTP.
- `user_agent` : agent utilisateur.

Dans OpenSearch Dashboards, ouvrir **Dev Tools** et exécuter :

```json
PUT nginx-access
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "client_ip": { "type": "ip" },
      "method": { "type": "keyword" },
      "url": { "type": "keyword", "ignore_above": 2048 },
      "http_version": { "type": "keyword" },
      "status": { "type": "integer" },
      "bytes": { "type": "long" },
      "referer": { "type": "keyword", "ignore_above": 2048 },
      "user_agent": { "type": "text" }
    }
  }
}
```

Cette configuration définit explicitement les types des champs avant l'importation.

**Remarque :** lors de la réalisation initiale, les documents ont d'abord été indexés dans `nginx-logs`, puis copiés vers `nginx-access` avec l'API `_reindex`. Le nouvel index a alors reçu un mapping généré automatiquement.

Pour une nouvelle installation, il est préférable de créer directement `nginx-access` avec le mapping explicite ci-dessus.

Dans ce cas, les champs `method` et `url` sont directement de type `keyword`. Avec le mapping généré automatiquement lors de la réalisation initiale, les visualisations utilisent les sous-champs `method.keyword` et `url.keyword`.

## 8. Préparation des logs

Confidentialité : les fichiers de logs, y compris leur version assainie, ne sont pas publiés dans ce dépôt. Pour reproduire l'importation, il faut disposer d'un jeu de logs Nginx Combined dont l'utilisation est autorisée, puis le préparer avec les scripts fournis.

Le fichier :

```text
elk/samples/nginx-access-anonymized.log
```

contient les logs assainis utilisés pour la démonstration.

Depuis la racine du dépôt :

```bash
python3 elk/ingestion/import_nginx.py
```

Résultat attendu :

```text
Documents préparés : 14496
Lignes non reconnues : 0
```

Le script génère :

```text
elk/ingestion/nginx-bulk.ndjson
```

Ce fichier respecte le format attendu par l'API Bulk d'OpenSearch.

Chaque document est représenté par deux lignes :

1. Une ligne d'action d'indexation.
2. Une ligne contenant le document JSON.

Le fichier NDJSON intermédiaire n'est pas versionné dans Git.

## 9. Importation dans OpenSearch

Récupérer l'endpoint depuis Terraform :

```bash
cd elk/aws

export OPENSEARCH_ENDPOINT="https://$(terraform output -raw elasticsearch)"

cd ../..
```

Le préfixe `https://` est nécessaire car l'output Terraform `elasticsearch` contient uniquement le nom d'hôte.

Saisir le mot de passe administrateur sans l'afficher :

```bash
read -r -s -p "Mot de passe OpenSearch : " OPENSEARCH_PASSWORD
echo
```

Découper le fichier en lots de 500 documents :

```bash
mkdir -p elk/ingestion/batches

split -l 1000 -d -a 3 \
  elk/ingestion/nginx-bulk.ndjson \
  elk/ingestion/batches/batch-
```

Chaque document occupant deux lignes, un lot de 1 000 lignes contient au maximum 500 documents.

Importer les lots :

```bash
for file in elk/ingestion/batches/batch-*; do
  echo "Import : $(basename "$file")"

  curl --fail-with-body --silent --show-error \
    --user "oc-p5-admin:${OPENSEARCH_PASSWORD}" \
    -H "Content-Type: application/x-ndjson" \
    --data-binary "@${file}" \
    "${OPENSEARCH_ENDPOINT}/nginx-access/_bulk?filter_path=errors,took,items.*.error"

  echo
done
```

**Important :** les lignes d'action générées dans le fichier NDJSON doivent cibler `nginx-access` ou ne pas spécifier d'index. Si elles contiennent explicitement un autre index, il faut les corriger avant l'importation.

Vérifier que chaque réponse indique :

```json
{"errors": false}
```

Vérifier ensuite le nombre de documents :

```bash
curl --fail-with-body --silent --show-error \
  --user "oc-p5-admin:${OPENSEARCH_PASSWORD}" \
  "${OPENSEARCH_ENDPOINT}/nginx-access/_count"
```

Le champ `count` doit être égal à `14496`.

Une fois l'importation terminée, les données peuvent être consultées depuis **Discover** dans OpenSearch Dashboards.

**Remarque de sécurité :** l'option `curl --user` peut exposer temporairement les identifiants dans la liste des processus du système. Cette méthode est réservée à un environnement pédagogique contrôlé.

## 10. Création et restauration du dashboard

### Création de l'Index Pattern

Dans OpenSearch Dashboards :

1. Ouvrir **Management > Dashboards Management > Index patterns**.
2. Cliquer sur **Create index pattern**.
3. Saisir `nginx-access`.
4. Sélectionner `@timestamp` comme champ temporel.
5. Valider la création.

L'Index Pattern permet d'explorer les données dans Discover et de créer les visualisations.

### Visualisation 1 — Répartition des méthodes HTTP

Type : **Pie**, avec affichage **Donut**.

Configuration :

- Index Pattern : `nginx-access`.
- Métrique : `Count`.
- Agrégation : `Terms`.
- Champ : `method.keyword` dans le mapping automatiquement généré, ou `method` dans le mapping explicite.
- Taille : `10`.
- Tri : nombre de requêtes décroissant.

Le graphique présente la répartition des méthodes HTTP présentes dans les logs :

- GET
- HEAD
- POST
- PUT

Nom de la visualisation :

`Nginx - Répartition des méthodes HTTP`

### Visualisation 2 — Volume de données par tranche de 12 heures

Type : **Vertical Bar**.

Configuration :

- Index Pattern : `nginx-access`.
- Axe Y : agrégation `Sum`.
- Champ : `bytes`.
- Axe X : agrégation `Date Histogram`.
- Champ temporel : `@timestamp`.
- Intervalle : `12 hours`.

Chaque barre représente la somme des octets envoyés par le serveur HTTP pendant une période de 12 heures.

Nom de la visualisation :

`Nginx - Volume de données par tranche de 12h`

### Visualisation 3 — Top 5 des requêtes par tranche de 12 heures

Type : **Vertical Bar**, avec affichage empilé.

Configuration :

- Index Pattern : `nginx-access`.
- Axe Y : `Count`.
- Première agrégation : `Split series`.
- Type : `Terms`.
- Champ : `url.keyword` dans le mapping automatiquement généré, ou `url` dans le mapping explicite.
- Taille : `5`.
- Tri : nombre de requêtes décroissant.
- Deuxième agrégation : `X-axis`.
- Type : `Date Histogram`.
- Champ : `@timestamp`.
- Intervalle : `12 hours`.
- Mode d'affichage : `Stacked`.

L'ordre des agrégations est important : les cinq URL les plus fréquentes sont sélectionnées sur l'ensemble de la période, puis leur activité est représentée par intervalles de 12 heures.

Les barres empilées permettent de visualiser le cumul des requêtes de ces cinq URL pour chaque période.

Nom de la visualisation :

`Nginx - Top 5 des requêtes par tranche de 12h`

### Dashboard final

Les trois visualisations sont regroupées dans un dashboard nommé :

**Nginx - Monitoring HTTP (version finale)**

Le dashboard permet d'analyser les méthodes HTTP utilisées, le volume de données transférées et les URL les plus sollicitées.

Les logs couvrent une période historique allant de juin à août 2024. Pour afficher les données, sélectionner une plage temporelle allant du **1er juin au 1er septembre 2024**.

### Restauration des objets

Le fichier `elk/export.ndjson` contient :

- 1 Index Pattern `nginx-access`.
- 3 visualisations.
- 1 dashboard `Nginx - Monitoring HTTP (version finale)`.
- Les métadonnées de l'export.

Pour restaurer le dashboard :

1. Se connecter à OpenSearch Dashboards.
2. Ouvrir **Management > Dashboards Management > Saved Objects**.
3. Cliquer sur **Import**.
4. Sélectionner le fichier `elk/export.ndjson`.
5. Confirmer l'importation des objets et de leurs dépendances.

**Important :** le fichier NDJSON contient les objets de visualisation, mais pas les documents de l'index. Il faut donc créer l'index et importer les logs avant de restaurer le dashboard.

Le mapping de l'index restauré doit également être compatible avec les champs utilisés par les visualisations.

## 11. Traitement des données

Le fichier source Nginx contenait des adresses IP publiques et certaines URL susceptibles de contenir des informations sensibles.

Un script `anonymize_nginx.py` a été développé pour produire un jeu de démonstration assaini.

Les transformations comprennent :

- Remplacement des adresses IP par des adresses privées fictives.
- Suppression des paramètres des URL.
- Remplacement des segments numériques dans les chemins.
- Remplacement des segments URL longs.
- Suppression des valeurs Referer et User-Agent.

Le format Nginx Combined est conservé afin de permettre l'analyse des logs avec le script d'importation.

Ces transformations réduisent les risques de divulgation, mais ne garantissent pas une anonymisation complète.

Le jeu de données doit être examiné avant toute diffusion publique. Les adresses IP fictives restent notamment stables au sein du fichier, ce qui permet de distinguer les clients simulés.

Le fichier source original n'est pas versionné.

## 12. Sécurité

Les mesures mises en œuvre comprennent :

- Authentification administrateur OpenSearch.
- Accès réseau limité à une adresse IPv4 autorisée.
- Chiffrement des données au repos.
- Chiffrement des communications entre nœuds.
- Accès HTTPS.
- Variables Terraform sensibles pour les secrets.
- Exclusion des fichiers Terraform State du dépôt Git.
- Exclusion des logs originaux et des fichiers temporaires d'importation.
- Préparation d'un échantillon de logs assaini.

Les secrets Terraform peuvent être présents dans le State, même lorsque les variables sont déclarées `sensitive`.

Les fichiers State ne doivent donc jamais être publiés.

L'environnement est destiné à un exercice pédagogique. Pour une infrastructure de production, il faudrait notamment renforcer la gestion des secrets, les permissions IAM, la supervision et les mécanismes de contrôle d'accès.

## 13. Destruction de l'infrastructure

Amazon OpenSearch Service est une ressource facturée tant que le domaine existe.

Après avoir exporté le dashboard, enregistré les captures d'écran et sauvegardé les fichiers nécessaires, l'infrastructure peut être détruite.

Depuis la racine du dépôt :

```bash
cd elk/aws
```

Configurer le profil AWS :

```bash
export AWS_PROFILE=terraform-oc-p5
```

Si les variables Terraform ne sont plus présentes dans l'environnement, les définir à nouveau avant de lancer la destruction.

Vérifier le plan de destruction :

```bash
terraform plan -destroy
```

Vérifier que les ressources affichées correspondent uniquement à l'infrastructure de l'exercice.

Lancer ensuite :

```bash
terraform destroy
```

Confirmer la destruction après vérification.

Contrôler enfin l'état Terraform :

```bash
terraform state list
```

La commande ne doit retourner aucune ressource si toutes les ressources gérées par cet état ont été supprimées.

La suppression du domaine OpenSearch entraîne également la suppression des documents indexés. Les fichiers locaux, les scripts et l'export du dashboard restent disponibles pour reconstruire l'environnement.

## 14. Résultat

L'exercice a permis de :

- Provisionner une infrastructure cloud avec Terraform.
- Déployer un domaine Amazon OpenSearch Service dans la région AWS Paris.
- Préparer un échantillon assaini de logs HTTP Nginx.
- Indexer et analyser 14 496 requêtes HTTP.
- Créer un index `nginx-access`.
- Explorer les données dans OpenSearch Dashboards.
- Créer un diagramme en donut de répartition des méthodes HTTP.
- Créer un histogramme du volume de données envoyé par tranches de 12 heures.
- Créer un histogramme empilé du Top 5 des requêtes par tranches de 12 heures.
- Construire un dashboard de monitoring HTTP.
- Exporter les objets OpenSearch Dashboards pour une restauration ultérieure.
- Préparer les captures d'écran demandées pour les livrables OpenClassrooms.
- Documenter le déploiement, l'importation des données, la restauration et la destruction de l'infrastructure.

Cette réalisation illustre l'utilisation d'une infrastructure cloud provisionnée en Infrastructure-as-Code pour centraliser, analyser et visualiser des logs applicatifs.
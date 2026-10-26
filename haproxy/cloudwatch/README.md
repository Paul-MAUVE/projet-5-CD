# Supervision HAProxy avec Amazon CloudWatch

## Objectif

Mettre en place une supervision de l'infrastructure HAProxy déployée sur AWS afin de surveiller les performances des instances EC2 et de centraliser les journaux.

Cette partie constitue un complément à l'exercice 3 du projet 5 OpenClassrooms.

## 1. Surveillance des métriques CPU

Utilisation d'Amazon CloudWatch Metrics pour observer et comparer la consommation CPU des trois instances EC2 :

- HAProxy
- Webserver 0 (Nginx)
- Webserver 1 (Nginx)

## 2. Configuration d'une alarme

Création de l'alarme `OC-P5-HAProxy-HighCPU` avec les paramètres suivants :

- Métrique : `CPUUtilization`
- Seuil : supérieur à 70 %
- Période : 5 minutes
- Évaluation : 2 périodes consécutives
- État observé : `OK`

L'objectif était de détecter une utilisation CPU anormalement élevée. Aucun déclenchement de l'alarme par une surcharge CPU n'a été testé.

## 3. Centralisation des logs HAProxy

Installation de l'Amazon CloudWatch Agent sur l'instance HAProxy.

Un rôle IAM associé à la politique `CloudWatchAgentServerPolicy` a permis à l'agent de communiquer avec CloudWatch sans utiliser de clés AWS permanentes.

Configuration de l'agent :

- Fichier surveillé : `/var/log/haproxy.log`
- Groupe CloudWatch Logs : `/oc-p5/haproxy`
- Flux de journaux : `{instance_id}`
- Région AWS : `eu-west-3` (Paris)
- Conservation : 7 jours

Le fichier `amazon-cloudwatch-agent.json` contient la configuration utilisée.

## 4. Résultats observés

Les journaux CloudWatch ont permis de vérifier :

- La distribution des requêtes HTTP entre les deux serveurs Nginx.
- La détection automatique de l'indisponibilité de `webserver0` (`DOWN`).
- Le maintien d'un serveur disponible pendant la panne.
- La réintégration automatique de `webserver0` après son rétablissement (`UP`).

Le fichier `log-events-anonymized.csv` contient 146 événements exportés depuis CloudWatch Logs, dont les événements de panne et de rétablissement.

Les huit adresses IP publiques détectées ont été remplacées par des identifiants anonymisés. Les adresses IP privées des serveurs ont été conservées pour faciliter la compréhension de l'architecture.

## 5. Nettoyage des ressources AWS

Après les tests :

- Les instances EC2 ont été détruites avec Terraform.
- L'alarme CloudWatch a été supprimée.
- Le groupe CloudWatch Logs a été supprimé.
- Le rôle IAM dédié a été supprimé.

Ce nettoyage permet d'éviter de conserver inutilement des ressources AWS facturables.

## Fichiers

| Fichier | Description |
|---|---|
| `amazon-cloudwatch-agent.json` | Configuration de l'agent CloudWatch |
| `log-events-anonymized.csv` | Export anonymisé des événements HAProxy |
| `README.md` | Documentation de la supervision |

**Remarque :** l'infrastructure AWS n'est plus active. Les fichiers conservés permettent de présenter la configuration et les résultats obtenus sans redéploiement.

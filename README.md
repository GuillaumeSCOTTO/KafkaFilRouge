![Alt text](https://github.com/GuillaumeSCOTTO/KafkaFilRouge/blob/092844f85c073a33bafaf801a5ea133d72d90255/pictures/structure.png)

Commande pour lancer le projet : docker-compose up

Le Producer envoie les données automatiquement.

Les consommeurs les traitent automatiquement.

Attendre quelques minutes après le docker compose up pour voir les résultats dans le conteneur aggregator: 

docker exec -it aggregator bash

puis 


cat results.txt

Le projet contient 8 conteneurs :
- Zookeeper
- Kafka
- Un premier extracteur de métadonnée (offenseval)
- Un deuxième extracteur de métadonnée (offenseval)
- Un producer qui envoie les données
- Un aggregator qui aggrège les résultats des modèles (= les métadonnées)
- Un elasticsearch qui va stocker les données
- Un kibana pour visualiser les doonnées
=======

requête pour lire les données de l'index "pfr" :

curl -XGET "http://localhost:9200/pfr/_search?pretty=true" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_all": {}
  }
}
'
remplacer localhost par l'adresse IP de elastic si reqûete faite dans un conteneur

requête pour lire un document par son id (timestamp) : 

curl -XGET "http://localhost:9200/pfr/_doc/{document_id}?pretty=true"


accès Kibana (le chargement est long) : http://localhost:5601/
##Access VM : ssh ubuntu@137.194.211.107

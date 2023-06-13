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


accès Kibana (le chargement est long) : http://localhost:5601/
##Access VM : ssh ubuntu@137.194.211.107

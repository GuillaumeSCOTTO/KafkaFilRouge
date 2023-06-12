Commande pour lancer le projet : docker-compose up

Le Producer envoie les données automatiquement.

Les consommeurs les traitent automatiquement.

Attendre quelques minutes après le docker compose up pour voir les résultats dans le conteneur aggregator: 

docker exec -it aggregator bash

puis 


cat results.txt

Le projet contient 7 conteneurs :
- Zookeeper
- Kafka
- Un premier extracteur de métadonnée (offenseval)
- Un deuxième extracteur de métadonnée (offenseval)
- Un producer qui envoie les données
- Un aggregator qui aggrège les résultats des modèles (= les métadonnées)
- Un elasticsearch qui va stocker les données
=======


Zookeeper
Kafka
Un premier extracteur de métadonnée (offenseval)
Un deuxième extracteur de métadonnée (offenseval)
Un producer qui envoie les données
Un aggregator qui aggrège les résultats des modèles (= les métadonnées)
Delete all unused containers : docker rm $(docker ps -a -f status=exited -q)

Delete all images : docker rmi $(docker images -a -q)

Access VM : ssh ubuntu@137.194.211.107

<<<<<<< HEAD

=======
Activate the venv for Python source test/bin/activate
>>>>>>> origin/antoine

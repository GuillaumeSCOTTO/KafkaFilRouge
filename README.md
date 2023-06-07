Commande pour lancer le projet : 
docker-compose up

Le Producer doit être lancé en ligne de commande : 
python code/producer/producer.py data/data.csv my_stream 10

L'aggrégateur doit être lancé en ligne de commande :
python code/producer/aggregation.py

Le projet contient 4 conteneurs :
- Zookeeper
- Kafka
- Un premier extracteur de métadonnée (offenseval)
- Un deuxième extracteur de métadonnée (offenseval)

Delete all unused containers :
docker rm $(docker ps -a -f status=exited -q)

Delete all images :
docker rmi $(docker images -a -q)

Access VM : 
ssh ubuntu@137.194.211.107
- Activate the venv for Python
	source test/bin/activate



# Infrastructure de traitement et d'analyse de Tweets

Ce repo a été réalisé dans le cadre du projet fil rouge du Mastère spécialisé Big Data de Télécom Paris en collaboration avec Airbus Defence&Space.

L'objectif est d'extraire des métadonnées de Tweets grâce à des modèles de langue tel qu'un score de sentiment et d'offense pour ensuite suivre leur évolution et potentiellement identifier une campagne de désinformation.

Deux métadonnées sont extraites, une amélioration pourra être d'apporter de nouveaux modèles pour l'extraction d'autres métadonnées. Ce Markdown contient les explication nécessaires pour l'ajout de nouveaux modèles.

![Alt text](https://github.com/GuillaumeSCOTTO/KafkaFilRouge/blob/a734323b0c0c5c4a181aa88d18ecb5f1f17d53aa/pictures/structure.png)

Le projet a entièrement été réalisé avec ces technologies : 
- **Python** pour la partie script
- **Docker** pour assurer la portabilité et le déploiement
- **Apache Kafka** pour créer le streaming de données et assurer une scalabilité du projet
- **ElasticSearch** et **Kibana** pour stocker et analyser aisément les métadonnées extraites


## Sommaire

1. [Lancement et utilisation du projet](#lancement-et-utilisation-du-projet)
2. [Configuration](#configuration)
    <ol type="a">
	 <li>Fichier de données</li>
	 <li>Ajout d'un consumer (métadonnée)</li>
	 <li>Scale docker-compose</li>
	 <li>Modifications du dashboard Kibana</li>
	</ol>
3. [Informations supplémentaires](#informations-supplémentaires)


## 1. Lancement et utilisation du projet

Seul **Docker** a besoin d'être installé sur la machine.

Le projet a été testé sur :
- Windows 10 avec Docker Desktop installé  
- Mac puce M1/M2
 
Il est recommandé d'avoir :
- au moins 30Go de disque mémoire disponible
- au moins 8Go de RAM

Liste des différents conteneurs : 
- Zookeeper
- Kafka
- Producer : crée le streaming des données à partir du fichier CSV
- Consumer Offense : ajoute un score d'offense aux tweets
- Consumer Sentiment : ajoute un socre de sentiments aux tweets
- Aggregator : permet d'aggréger les données d'un tweet en un seul json
- ElasticSearch
- Kibana

Pour lancer le projet, il suffit de se placer dans le répertoire du repo cloné et de lancer : 
```docker-compose up```
Le lancement peut mettre plusieurs minutes, il faut bien attendre que tous les conteneurs soient *up* avant d'accéder aux fonctionnalités de l'application.

Chaque container scripté avec Python possède un document de logs qui peut être accéder via les commandes : 
- ```docker exec -it {ID/nom du conteneur} bash```
- ```cat logs_{nom_consumer}.logs```

Un dashboard est accessible via Kibana en local via l'URL suivant : [Kibana Dashboard](http://localhost:5601) .

Il suffit ensuite d'aller dans la rubrique *Dashboard* et cliquer sur *PFR*.

Il est possible d'intéragir avec la base de donnée dans l'outil *Dev Tools* de Kibana.

- Retourne 10 documents dans l'index *pfr* :
```
GET /pfr/_search{  
	"query": {    
		"match_all": {}  
	}
}
```

- Retourne les documents dans l'index *pfr* matchant le *pseudo* *scotthamilton* :
```
GET /pfr/_search{  
	"query": {    
		"match": {      
			"pseudo": "scotthamilton"    
		}  
	}
}
```


## 2. Configuration

### i. Fichier de données

Le jeu de données initial provient de [sentiment140](https://www.kaggle.com/datasets/kazanova/sentiment140) situé dans */data/*.

Il est possible de modifier le CSV de données se trouvant dans le chemin suivant */data/* à condition de respecter certaines conditions :
- Nommé le fichier *data.csv*, peut être modifié dans le *docker-compose.yml* sinon
- Le fichier n'a pas de ligne header
- Le fichier comprend un champ **timestamp** sous **format string** et **Unix Timestamp**
- Préciser dans le *.env* les champs à conserver et leur position dans le CSV

![Alt text](https://github.com/GuillaumeSCOTTO/KafkaFilRouge/blob/a734323b0c0c5c4a181aa88d18ecb5f1f17d53aa/pictures/env_file.PNG)

- Colonne du champ **timestamp** (1 => première colonne) dans la variable *TIMESTAMP_FIELD*
- Colonne des autres champs et leur nom dans la variable *INITIAL_FIELDS*
	
Un champ supplémentaire *SPEED* dans le conteneur *producer* sert à accélérer le stream des tweets par rapport aux Timestamps initiaux.

Par soucis d'utilisation, les timestamp sont convertis en temps réel. Seul la différence de temps entre deux tweets est respectée.


### ii. Ajout d'un consumer (métadonnée)

Les modèles ajoutés ne peuvent qu'effectuer de l'inférence sur un champ texte.

Voici à quoi ressemble la construction d'un Consumer dans le *docker-compose.yml* : 

![Alt text](https://github.com/GuillaumeSCOTTO/KafkaFilRouge/blob/a734323b0c0c5c4a181aa88d18ecb5f1f17d53aa/pictures/consumer.PNG)

Plusieurs champs sont à renseigner : 
- *INFERENCE_PYTHON_FILE* : nom du fichier python comportant deux fonctions, il doit respecté la convention suivante => *{NomMétadonnée}_inference.py*, le nom de la métadonnée se retrouve dans la variable du fichier *.env*.
	- *inference* pour prédire sur un champ texte
	- *load_model* pour charger le modèle
- *INFERENCE_PYTHON_MODEL* : nom du modèle sous format *.pth* ou *.pth.tar* 
- *INFERENCE_CLASSIFIER_NAME* : *None* si le modèle possède une classe sinon le nom de la classe

![Alt text](https://github.com/GuillaumeSCOTTO/KafkaFilRouge/blob/a734323b0c0c5c4a181aa88d18ecb5f1f17d53aa/pictures/consumer_files.PNG)

Les fichiers du modèles doivent être stockés dans un nouveau répertoire à la racine de */code/*, ce répertoire doit contenir :
- fichier *.py* contenant les deux fonctions
- le modèle en *.pth* ou *.pth.tar*
- le *requirements.txt* contenant les dépendances python du modèle
- le *Dockerfile* afin de créer l'image

Il faut que le nom du répertoire du nouveau modèle soit le même dans la variable *dockerfile* du *docker-compose.yml*.

![Alt text](https://github.com/GuillaumeSCOTTO/KafkaFilRouge/blob/a734323b0c0c5c4a181aa88d18ecb5f1f17d53aa/pictures/consumer_dockerfile.PNG)

Dans ce *Dockerfile*, on retrouve les commandes :
- d'installation des dépendances => le nom du répertoire doit être modifié
- de copie des 2 fichiers du modèle => les nom du répertoire et des fichiers doivent être modifiés

Enfin dans le fichier *.env* :
- la variable *CONSUMERS_LIST* est un dictionnaire contenant:
	- en clés : les noms des métadonnées en relation avec le nom du fichier *.py*
	- en valeurs : le type de donnée retournée par le modèle ("integer", "float" ou "text")
	
Le nouveau modèle est maintenant normalement configuré !!


### iii. Scale docker-compose

Il est possible d'intégrer de la scalabilité horizontale pour partager la charge sur un Consumer avec une option dans la configuration d'un conteneur dans le *docker-compose.yml*.

Le cas d'utilisation de cette feature peut être dû à un temps d'inférence trop long sur un des Consumers.

```
deploy:
	mode: replicated
	replicas: 2
```

Il faut en plus lancer le projet avec la commande : ```docker-compose --compatibility up``` car aucun orchestrateur n'est utilisé.

Cette fonctionnalité permet par exemple de doublé le nombre de conteneur pour un Consumer et donc diviser la charge d'inférence entre les deux.
Les conteneurs répliqués ont exactement les mêmes caractéristiques.

Pour ne pas l'utiliser il faut commenter cette partie dans le *docker-compose.yml*.


### iv. Modifications du dashboard Kibana

Sur le dashboard par défaut on retrouve 4 lens :
- Count of records : nombre de tweets reçus dans l'intervalle de temps sélectionné
- Average of Sentiment every 10 min
- Average of Offense every 10 min
- Number of tweets per 10 min

![Alt text](https://github.com/GuillaumeSCOTTO/KafkaFilRouge/blob/a734323b0c0c5c4a181aa88d18ecb5f1f17d53aa/pictures/dashboard_kibana.PNG)

Il est possible de modifier les seuils de chacun des 3 graphiques en modifiant la Lens puis en allant dans *Reference Lines* et cliquer sur *Vertical Left Axis*, *Reference line value* permet ensuite de modifier la valeur du seuil.

Il est aussi possible de modifier l'intervalle de temps d'aggrégation en cliquant cette fois-ci sur *timestamp* dans *horizontal axis* puis modifier le *minimum interval*, il est par défaut paramétré à 10 minutes.

L'ajout de nouvelles Lens est bien évidemment autorisé.


## 3. Informations supplémentaires

Le répertoire */elasticsearch/* stocke les configurations et les données dont :
- le dashboard *PFR*
- index pattern *pfr*
- les données sont vidées à chaque nouveau lancement du ```docker-compose up``` dans le script *aggregator.py*

Dans chaque DockerFile faisant intervenir Kafka (Ex: producer, aggregator, consumers), une commande commençant par *apt-get* est nécessaire pour l'utilisation de Kafka sur Mac, elle n'est pas nécessaire sur Windows et peut donc être commentée.


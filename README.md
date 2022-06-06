# Help Sardoche !

Sardoche est parti en Corée et ça va mal ! Il faut l'aider à comprendre le matchmaking, ci-gît une veine tentative.

## Ci-gît une veine tentative... Pourquoi ?

[L'API de Riot](https://developer.riotgames.com) ne permet pas de récupérer les données au moment du matchmaking, par conséquent on peut pas sur cette base collecter de la donnée pertinente.

Il faudrait en temps réel récupérer de la data après un matchmaking et la recenser au fil de l'eau.

## Cependant...

Ce projet recense tout de même l'évolution des joueurs, ainsi indiquer la propension de smurfs dans les parties et la récurrence du placement de Sardoche dans les équipes (si la tendance était de le mettre dans un 1v9, un 5v5 ou un 9v1).

## Init

- Créé un compte sur [Riot](https://developer.riotgames.com)
- Récupère ta clé API
- créé un fichier `.env` en ajoutant `LOL_API_KEY=<ta clé API>` et `SUM_NAME=안드래아스`

Lance `python3 gen_data.py` pour récupérer de la data.

Lance `python3 graph_data.py` pour générer des graphes.

Cela va récupérer les 100 derniers matchs de Sardoche et générer un `sardhelp.csv`

Made with 🤫 in [Twitch Live](https://www.twitch.tv/videos/1495696626)

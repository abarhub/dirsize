# dirsize

Outils pour analyser la taille des répertoires

Pout l'utiliser, il faut récupérer le zip, le décompresser, modifier le fichier config.ini et exécuter :
```shell
python config.ini.py
```

Exemple de fichier config :
```ini
[CONFIG]
repertoire_racine=/home/test
repertoire=/home/test/apache-tomcat-9.0.37\webapps
repertoire_glob=*.js,*.html
liste_repertoire=/home/test/apache-tomcat-9.0.37\webapps
repertoire_resultat=out

[LOGGING]
log_file=logs/dirsize.log
# DEBUG, INFO, WARN, ERROR
log_level=INFO
```

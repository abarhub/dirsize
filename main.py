import csv
import fnmatch
import logging
import operator
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path


class PathInfo:
    size = 0

    def __str__(self):
        typeClasse = type(self).__name__
        return f'{typeClasse}(size:{self.size})'

    def __repr__(self):
        return self.__str__()

    def ajoute(self, path, size):
        pass

    def resultat(self):
        return [self.size]


class PathInfoSimple(PathInfo):
    path = None

    def __init__(self, path):
        assert path != None
        assert isinstance(path, Path), f'type path:{type(path)}'
        self.path = path

    def ajoute(self, path, size):
        if startWith(path, self.path):
            self.size += size

    def resultat(self):
        return [[str(self.path), self.size, format_bytes2(self.size)]]


class PathInfoGlob(PathInfo):
    glob = None

    def __init__(self, glob):
        assert glob != None
        self.glob = glob

    def ajoute(self, path, size):
        if fnmatch.fnmatch(path, self.glob):
            self.size += size

    def resultat(self):
        return [[self.glob, self.size, format_bytes2(self.size)]]


class PathInfoList(PathInfo):
    path = None
    listPath = {}
    fileSize = 0

    def __init__(self, path):
        assert path != None
        assert isinstance(path, Path), f'type path:{type(path)}'
        self.path = path

    def ajoute(self, path, size):
        if str(path).startswith(str(self.path)):
            self.size += size
            (nom, suite) = self.decoupe(path)
            if path.is_dir:
                if nom in self.listPath:
                    v = self.listPath[nom]
                    v += size
                    self.listPath[nom] = v
                else:
                    self.listPath[nom] = size
            else:
                self.fileSize += size

    def decoupe(self, path):
        if path.parent == self.path:
            return (path.name, '')
        else:
            tmp = path
            suite = ''
            while tmp.parent != self.path:
                suite = tmp.name + '/' + suite
                tmp = tmp.parent
            return (tmp.name, suite)

    def __str__(self):
        typeClasse = type(self).__name__
        return f'{typeClasse}(listPath:{self.listPath};fileSize:{self.fileSize})'

    def resultat(self):
        liste = []
        for key, value in self.listPath.items():
            liste.append([str(self.path / key), value, format_bytes2(value)])
        liste.append([str(self.path / '*'), self.fileSize, format_bytes2(self.fileSize)])
        return liste


def format_bytes2(size):
    val, label = format_bytes(size * 1.0)
    if val.is_integer():
        return f'{val} {label}'
    else:
        return f'{val:.2f} {label}'


def format_bytes(size):
    # 2**10 = 1024
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'kilo', 2: 'mega', 3: 'giga', 4: 'tera'}
    while size > power:
        size /= power
        n += 1
    return size, power_labels[n] + 'bytes'


def startWith(pathComplet, path):
    if path == None or pathComplet == None:
        return False
    p1 = pathComplet.resolve()
    p2 = path.resolve()
    if p1.samefile(p2):
        return True
    p1 = p1.parent
    while p1 != None:
        if p1.samefile(p2):
            return True
        if p1.parent.samefile(p1):
            break
        p1 = p1.parent

    return False


def parcourt(repertoire, dico):
    for child in repertoire.iterdir():
        if (child.is_dir()):
            parcourt(child, dico)
        else:
            size = child.stat().st_size
            # print(child, size)
            logging.debug(f'fichier: {child} size: {size}')
            for key, value in dico.items():
                value.ajoute(child, size)


def parcourt_complet():
    config_object = ConfigParser()
    config_object.read("config.ini")

    config = config_object["CONFIG"]

    repertoire = config['repertoire_racine']
    path = Path(repertoire).resolve()
    assert path.is_absolute()
    assert path.is_dir()

    repertoireResultat = config['repertoire_resultat']

    dico = {}
    dico[repertoire] = PathInfoSimple(path)

    rep = config['repertoire']
    liste_repertoire = rep.split(',')

    for rep2 in liste_repertoire:
        path2 = Path(rep2).resolve()
        dico[path2] = PathInfoSimple(path2)

    rep = config['repertoire_glob']
    liste_repertoire = rep.split(',')

    for rep2 in liste_repertoire:
        dico[rep2] = PathInfoGlob(rep2)

    rep = config['liste_repertoire']
    liste_repertoire = rep.split(',')

    for rep2 in liste_repertoire:
        path2 = Path(rep2).resolve()
        dico[rep2] = PathInfoList(path2)

    parcourt(path, dico)
    logging.debug(dico)

    liste_resultat = []
    for key, value in dico.items():
        liste = value.resultat()
        for item in liste:
            liste_resultat.append(item)

    logging.debug(f'liste non trie={liste_resultat}')

    # trie de la liste
    liste_resultat = sorted(liste_resultat, key=operator.itemgetter(0))

    logging.debug(f'liste trie={liste_resultat}')

    dateFormat = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    fichierResultat = f'{repertoireResultat}/resultat_{dateFormat}.csv'

    logging.info(f'resultat={liste_resultat}')

    print(f'fichier={fichierResultat}')
    logging.info(f'fichier={fichierResultat}')

    # génération du fichier csv
    with open(fichierResultat, 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        spamwriter.writerow(['Repertoire', 'taille octet', 'taille'])
        for item in liste_resultat:
            spamwriter.writerow(item)


def parseLogConfig():
    config_object = ConfigParser()
    config_object.read("config.ini")

    config = config_object["LOGGING"]
    logfile = config['log_file']
    loglevel = config['log_level']

    level = logging.INFO
    if loglevel == 'DEBUG':
        level = logging.DEBUG
    elif loglevel == 'INFO':
        level = logging.INFO
    elif loglevel == 'WARN':
        level = logging.WARN
    elif loglevel == 'ERROR':
        level = logging.ERROR

    logging.basicConfig(filename=logfile, level=level,
                        format='%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s')


if __name__ == '__main__':
    parseLogConfig()
    logging.info("demarrage")
    parcourt_complet()
    logging.info("fin")

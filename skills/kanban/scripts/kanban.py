#!/usr/bin/env python3
"""Backlog local en Markdown, façon Jira : un ticket par fichier, un tableau kanban, la synchro Jira.

Le backlog d'un dépôt vit dans docs/backlog/ : config.yml, README.md et tickets/<CLE>-<titre>.md.
Chaque ticket commence par un en-tête YAML simple (une ligne « clé: valeur » par champ), puis son
texte en Markdown : Résumé, Notes de cadrage, Suivi. Les fichiers sont la source de vérité ; ce
script ne fait que les lire, les vérifier et y changer quelques champs.

Usage :
  kanban.py [--dossier DIR] init --projet NOM --prefixe PRE
  kanban.py [--dossier DIR] tableau [--epic CLE] [--tout]
  kanban.py [--dossier DIR] html [--sortie FICHIER] [--pas-ouvrir]
  kanban.py [--dossier DIR] serve [--port 8765] [--pas-ouvrir]
  kanban.py [--dossier DIR] verifier
  kanban.py [--dossier DIR] nouveau "Titre" --type story [--epic CLE] [--rang N] [--statut S] [--resume TEXTE]
  kanban.py [--dossier DIR] deplacer CLE STATUT [--motif TEXTE]
  kanban.py [--dossier DIR] a-pousser [--json]
  kanban.py [--dossier DIR] synchro CLE --jira CLE-JIRA

Sans --dossier : docs/backlog à la racine du dépôt git qui contient le répertoire courant.
Sans commande : tableau.

« serve » sert aussi, en lecture seule sur /doc/, la documentation du projet : les fichiers .md des
dossiers de la clé documentation de config.yml, depuis la racine du dépôt (défaut : docs/specs, les fiches,
et docs/documentation). Le champ fiche d'un ticket mène à la page de sa fiche.
Tests : python3 -I -B scripts/selftest.py
"""
import argparse
import collections
import datetime as dt
import hashlib
import html
import http.server
import json
import re
import sys
import tempfile
import unicodedata
import urllib.parse
import webbrowser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
MODELE_README = SKILL_DIR / "assets" / "README.md"

STATUTS = {
    "a-cadrer": "À cadrer",
    "en-cadrage": "En cadrage",
    "pret": "Prêt",
    "en-cours": "En cours",
    "en-revue": "En revue",
    "termine": "Terminé",
    "abandonne": "Abandonné",
}
COLONNES = [s for s in STATUTS if s != "abandonne"]
# Statuts où une story devrait avoir sa fiche.
STATUTS_AVEC_FICHE = ("pret", "en-cours", "en-revue", "termine")
TYPES = {"epic": "Epic", "story": "Story", "tache": "Tâche", "spike": "Spike", "bug": "Bug"}
OBLIGATOIRES = ("cle", "titre", "type", "statut", "cree")
ORDRE = ("cle", "titre", "type", "statut", "epic", "rang", "fiche", "bloque_par",
         "jira", "synchro_jira", "empreinte_jira", "cree")
# Champs dont un changement doit repartir dans Jira (avec le corps hors Suivi et la fiche).
POUSSES = ("titre", "type", "statut", "epic", "rang", "fiche", "bloque_par")
# Dossiers servis par « serve » quand config.yml n'a pas de clé documentation.
DOCUMENTATION_PAR_DEFAUT = ("docs/specs", "docs/documentation")
SECTION_RESUME = "Résumé"
SECTION_NOTES = "Notes de cadrage"
SECTION_SUIVI = "Suivi"
COMMENTAIRE_NOTES = (
    "<!-- Brouillon. Une note par échange, la plus récente à la fin : la question telle qu'elle "
    "a été posée, la réponse telle qu'elle a été donnée. On ajoute, on ne réécrit pas. "
    "On cadrera en arrivant sur le ticket. -->"
)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class ErreurBacklog(Exception):
    pass


# ---------------------------------------------------------------- en-tête YAML minimal

def sans_commentaire(valeur):
    """Retire un commentaire de fin de ligne (« # … »), comme YAML, hors des guillemets."""
    if valeur[:1] in ('"', "'"):
        guillemet, i = valeur[0], 1
        while i < len(valeur):
            if guillemet == '"' and valeur[i] == "\\":
                i += 2
                continue
            if valeur[i] == guillemet:
                if guillemet == "'" and valeur[i + 1:i + 2] == "'":
                    i += 2
                    continue
                return valeur[:i + 1]
            i += 1
        return valeur
    return re.split(r"\s+#", valeur, maxsplit=1)[0].rstrip()


def interpreter(valeur, source=""):
    """Valeur YAML simple : vide, chaîne (nue ou entre guillemets), entier, liste [a, b]."""
    valeur = sans_commentaire(valeur)
    if valeur in ("", "~", "null"):
        return None
    if len(valeur) >= 2 and valeur[0] == valeur[-1] == '"':
        try:
            return json.loads(valeur)
        except json.JSONDecodeError as exc:
            raise ErreurBacklog(f"{source} : chaîne mal formée {valeur} ({exc.msg})") from exc
    if len(valeur) >= 2 and valeur[0] == valeur[-1] == "'":
        return valeur[1:-1].replace("''", "'")
    if valeur.startswith("[") and valeur.endswith("]"):
        dedans = valeur[1:-1].strip()
        return [interpreter(v.strip(), source) for v in dedans.split(",")] if dedans else []
    if re.fullmatch(r"-?\d+", valeur):
        return int(valeur)
    return valeur


def formater(valeur):
    if valeur is None:
        return ""
    if isinstance(valeur, bool):
        return "true" if valeur else "false"
    if isinstance(valeur, int):
        return str(valeur)
    if isinstance(valeur, list):
        return "[" + ", ".join(formater(v) for v in valeur) + "]"
    texte = str(valeur)
    if (texte == "" or texte != texte.strip() or ": " in texte or " #" in texte
            or texte.endswith(":") or texte[0] in "[]{}\"'#&*!|>%@`,-?:"
            or re.fullmatch(r"-?\d+", texte)
            or texte.lower() in ("true", "false", "null", "yes", "no", "~")):
        return json.dumps(texte, ensure_ascii=False)
    return texte


def lire_texte(chemin):
    return chemin.read_text(encoding="utf-8").replace("\r\n", "\n")


def ecrire_texte(chemin, texte):
    chemin.write_text(texte if texte.endswith("\n") else texte + "\n", encoding="utf-8")


def lire_champs(lignes, source, premiere_ligne=1):
    champs = {}
    for numero, ligne in enumerate(lignes, premiere_ligne):
        if not ligne.strip() or ligne.lstrip().startswith("#"):
            continue
        cle, sep, valeur = ligne.partition(":")
        if not sep or not re.fullmatch(r"[a-z_][a-z0-9_-]*", cle.strip()):
            raise ErreurBacklog(f"{source}, ligne {numero} : « {ligne} » n'est pas de la forme clé: valeur")
        champs[cle.strip()] = interpreter(valeur.strip(), f"{source}, ligne {numero}")
    return champs


def bornes_entete(lignes, source):
    """Indice de la ligne --- qui ferme l'en-tête (la première ligne est ---)."""
    if not lignes or lignes[0].strip() != "---":
        raise ErreurBacklog(f"{source} : pas d'en-tête YAML (le fichier doit commencer par ---)")
    for i in range(1, len(lignes)):
        if lignes[i].strip() == "---":
            return i
    raise ErreurBacklog(f"{source} : en-tête YAML non fermé (--- manquant)")


# ---------------------------------------------------------------- sections Markdown

def est_cloture(ligne):
    return ligne.lstrip().startswith(("```", "~~~"))


def est_titre_2(ligne):
    return re.match(r"##\s+\S", ligne) is not None and not ligne.startswith("###")


def decouper(corps):
    """[(titre de niveau 2 ou None, [lignes])], sans tenir compte des titres dans les blocs de code."""
    parties = [[None, []]]
    dans_code = False
    for ligne in corps.split("\n"):
        if est_cloture(ligne):
            dans_code = not dans_code
        if not dans_code and est_titre_2(ligne):
            parties.append([ligne.lstrip("#").strip(), []])
        else:
            parties[-1][1].append(ligne)
    return parties


def section(corps, titre):
    for nom, lignes in decouper(corps):
        if nom == titre:
            return "\n".join(lignes)
    return None


def corps_sans(corps, titre):
    morceaux = []
    for nom, lignes in decouper(corps):
        if nom == titre:
            continue
        if nom is not None:
            morceaux.append(f"## {nom}")
        morceaux.extend(lignes)
    return "\n".join(morceaux)


def titres_3(texte):
    titres, dans_code = [], False
    for ligne in (texte or "").split("\n"):
        if est_cloture(ligne):
            dans_code = not dans_code
        elif not dans_code and ligne.startswith("### "):
            titres.append(ligne[4:].strip())
    return titres


# ---------------------------------------------------------------- tickets et backlog

class Ticket:
    def __init__(self, chemin, champs, corps):
        self.chemin = chemin
        self.champs = champs
        self.corps = corps

    def get(self, cle, defaut=None):
        valeur = self.champs.get(cle)
        return defaut if valeur is None else valeur

    @property
    def cle(self):
        return str(self.get("cle", ""))

    @property
    def titre(self):
        return str(self.get("titre", ""))

    @property
    def type(self):
        return str(self.get("type", ""))

    @property
    def statut(self):
        return str(self.get("statut", ""))

    @property
    def epic(self):
        return self.get("epic")

    @property
    def rang(self):
        rang = self.get("rang")
        return rang if isinstance(rang, int) else None

    @property
    def numero(self):
        trouve = re.search(r"-(\d+)$", self.cle)
        return int(trouve.group(1)) if trouve else 0

    @property
    def bloque_par(self):
        valeur = self.get("bloque_par", [])
        return valeur if isinstance(valeur, list) else [valeur]

    def notes(self):
        return titres_3(section(self.corps, SECTION_NOTES))

    def derniere_note(self):
        dates = [d.group(0) for d in (DATE.match(t) for t in self.notes()) if d]
        return max(dates) if dates else None


def racine_depot(depart):
    for dossier in [depart, *depart.parents]:
        if (dossier / ".git").exists():
            return dossier
    return None


def dossier_par_defaut():
    racine = racine_depot(Path.cwd().resolve())
    return (racine or Path.cwd()) / "docs" / "backlog"


def aujourdhui():
    return dt.date.today().isoformat()


def slug(texte, longueur=50):
    ascii_ = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    ascii_ = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_).strip("-").lower()
    return ascii_[:longueur].rstrip("-") or "ticket"


class Backlog:
    def __init__(self, dossier):
        self.dossier = dossier.resolve()
        if not (self.dossier / "config.yml").is_file():
            raise ErreurBacklog(
                f"pas de backlog dans {self.dossier} (config.yml absent). "
                "Lancer « kanban.py init --projet NOM --prefixe PRE », ou passer --dossier."
            )
        self.racine = racine_depot(self.dossier) or self.dossier.parent.parent
        self.config = lire_champs(lire_texte(self.dossier / "config.yml").split("\n"), "config.yml")
        self.tickets, self.erreurs = [], []
        for chemin in sorted((self.dossier / "tickets").glob("*.md")):
            try:
                lignes = lire_texte(chemin).split("\n")
                fin = bornes_entete(lignes, chemin.name)
                champs = lire_champs(lignes[1:fin], chemin.name, 2)
                self.tickets.append(Ticket(chemin, champs, "\n".join(lignes[fin + 1:])))
            except ErreurBacklog as exc:
                self.erreurs.append(str(exc))
        self.par_cle = {t.cle: t for t in self.tickets}

    @property
    def projet(self):
        return str(self.config.get("projet") or self.racine.name)

    @property
    def prefixe(self):
        return self.config.get("prefixe")

    def trouver(self, cle):
        ticket = self.par_cle.get(cle) or self.par_cle.get(cle.upper())
        if ticket is None:
            raise ErreurBacklog(f"aucun ticket {cle} dans {self.relatif(self.dossier)}")
        return ticket

    def prochaine_cle(self):
        if not self.prefixe:
            raise ErreurBacklog("config.yml n'a pas de prefixe")
        numeros = [t.numero for t in self.tickets]
        # Une clé n'est jamais réutilisée : on compte aussi les fichiers illisibles.
        for chemin in (self.dossier / "tickets").glob(f"{self.prefixe}-*.md"):
            trouve = re.match(rf"{re.escape(self.prefixe)}-(\d+)", chemin.name)
            if trouve:
                numeros.append(int(trouve.group(1)))
        return f"{self.prefixe}-{max(numeros, default=0) + 1}"

    def relatif(self, chemin):
        try:
            return str(Path(chemin).resolve().relative_to(Path.cwd().resolve()))
        except ValueError:
            return str(chemin)

    def chemin_fiche(self, ticket):
        fiche = ticket.get("fiche")
        return (self.racine / str(fiche)) if fiche else None

    def documentation(self):
        return Documentation(self.racine, dossiers_documentation(self.config))

    def tri(self, ticket):
        epic = self.par_cle.get(ticket.epic) if ticket.epic else None
        groupe = epic.numero if epic else (ticket.numero if ticket.type == "epic" else 10 ** 9)
        rang = -1 if ticket.type == "epic" else (ticket.rang if ticket.rang is not None else 10 ** 6)
        return (groupe, rang, ticket.numero)

    def enfants(self, epic):
        return [t for t in self.tickets if t.epic == epic.cle and t.statut != "abandonne"]

    def tranche(self, ticket):
        """« T3 » pour une story rangée dans une epic."""
        if ticket.type == "story" and ticket.epic and ticket.rang is not None:
            return f"T{ticket.rang}"
        return ""

    def empreinte(self, ticket):
        champs = {k: ticket.champs.get(k) for k in POUSSES}
        corps = corps_sans(ticket.corps, SECTION_SUIVI)
        corps = "\n".join(ligne.rstrip() for ligne in corps.strip().split("\n"))
        hache = hashlib.sha256()
        hache.update(json.dumps(champs, sort_keys=True, ensure_ascii=False).encode())
        hache.update(b"\0" + corps.encode())
        fiche = self.chemin_fiche(ticket)
        if fiche and fiche.is_file():
            hache.update(b"\0" + fiche.read_bytes())
        return hache.hexdigest()[:12]

    def etat(self):
        """Empreinte des fichiers lus par le tableau, pour le rechargement en direct."""
        hache = hashlib.sha256()
        fichiers = [self.dossier / "config.yml", *sorted((self.dossier / "tickets").glob("*.md"))]
        fichiers += [f for f in (self.chemin_fiche(t) for t in self.tickets) if f and f.is_file()]
        for fichier in fichiers:
            infos = fichier.stat()
            hache.update(f"{fichier}:{infos.st_mtime_ns}:{infos.st_size};".encode())
        return hache.hexdigest()[:16]


# ---------------------------------------------------------------- documentation

def dossiers_documentation(config):
    """Les dossiers de la clé documentation de config.yml, relatifs à la racine du dépôt."""
    dossiers = config.get("documentation")
    if dossiers is None:
        return list(DOCUMENTATION_PAR_DEFAUT)
    return [str(d) for d in dossiers] if isinstance(dossiers, list) else [str(dossiers)]


def descend_de_la_racine(relatif):
    """Vrai pour un chemin relatif qui ne remonte pas (..) : il désigne quelque chose sous la racine."""
    return not Path(relatif).is_absolute() and ".." not in Path(relatif).parts


def sous(chemin, dossier):
    try:
        chemin.relative_to(dossier)
        return True
    except ValueError:
        return False


class Documentation:
    """Les pages Markdown servies en lecture seule par « serve » : les fichiers .md des dossiers configurés."""

    def __init__(self, racine, dossiers):
        self.racine = racine.resolve()
        self.dossiers = dossiers

    def document(self, relatif):
        """Le fichier d'un chemin relatif à la racine, ou None s'il n'est pas à servir.

        Le fichier réel, liens symboliques suivis, doit être un .md sous la racine et sous un dossier de
        documentation : un lien ne fait pas sortir de la racine. Le chemin ne remonte pas (..) et n'est pas
        absolu : une page n'a qu'une adresse.
        """
        if not descend_de_la_racine(relatif):
            return None
        fichier = self.racine / relatif
        reel = fichier.resolve()
        a_servir = (fichier.suffix == reel.suffix == ".md" and reel.is_file() and sous(reel, self.racine)
                    and any(sous(reel, (self.racine / d).resolve()) for d in self.dossiers))
        return fichier if a_servir else None

    def sommaire(self):
        """Une rubrique par dossier de documentation, dans l'ordre de config.yml."""
        return [Rubrique(dossier, (self.racine / dossier).is_dir(), self.pages(dossier))
                for dossier in self.dossiers]

    def pages(self, dossier):
        """Les pages d'un dossier et de ses sous-dossiers, rangées comme un arbre de fichiers : celles d'un
        dossier, son point d'entrée en tête, avant celles de ses sous-dossiers. Seulement celles que
        document() accepte de servir."""
        pages = [Page(chemin, titre_de_page(lire_texte(f), f.name)) for chemin, f in self.fichiers(dossier)]
        return sorted(pages, key=lambda p: (Path(p.chemin).parent.parts, not p.est_point_d_entree,
                                            p.chemin.lower()))

    def fichiers(self, dossier):
        """(chemin depuis la racine, fichier) des .md d'un dossier et de ses sous-dossiers que document() sert."""
        if not descend_de_la_racine(dossier):
            return []
        chemins = sorted(f.relative_to(self.racine).as_posix() for f in (self.racine / dossier).rglob("*.md"))
        servis = ((chemin, self.document(chemin)) for chemin in chemins)
        return [(chemin, fichier) for chemin, fichier in servis if fichier]

    def etat(self):
        """Empreinte des pages servies, pour le rechargement en direct : elle change quand l'une change."""
        hache = hashlib.sha256()
        for dossier in self.dossiers:
            for chemin, fichier in self.fichiers(dossier):
                infos = fichier.stat()
                hache.update(f"{chemin}:{infos.st_mtime_ns}:{infos.st_size};".encode())
        return hache.hexdigest()[:16]


Rubrique = collections.namedtuple("Rubrique", "dossier existe pages")


class Page(collections.namedtuple("Page", "chemin titre")):
    @property
    def est_point_d_entree(self):
        """INDEX.md ou README.md : la page par laquelle on entre dans un dossier."""
        return Path(self.chemin).name.lower() in ("index.md", "readme.md")


def titre_de_page(texte, nom_du_fichier):
    """Le premier titre de niveau 1 d'un texte Markdown, ou à défaut le nom de son fichier."""
    for ligne in texte.split("\n"):
        titre_md = MD_TITRE.match(ligne)
        if titre_md and len(titre_md.group(1)) == 1:
            return titre_md.group(2)
    return nom_du_fichier


# ---------------------------------------------------------------- écriture dans un ticket

def modifier_champs(chemin, nouveaux):
    """Change ou ajoute des champs de l'en-tête sans toucher au reste du fichier."""
    lignes = lire_texte(chemin).split("\n")
    fin = bornes_entete(lignes, chemin.name)
    for cle, valeur in nouveaux.items():
        ligne = f"{cle}: {formater(valeur)}".rstrip()
        for i in range(1, fin):
            if re.match(rf"{re.escape(cle)}\s*:", lignes[i]):
                lignes[i] = ligne
                break
        else:
            position = 1
            rang_cle = ORDRE.index(cle) if cle in ORDRE else len(ORDRE)
            for i in range(1, fin):
                nom = lignes[i].partition(":")[0].strip()
                if nom in ORDRE and ORDRE.index(nom) < rang_cle:
                    position = i + 1
            if cle not in ORDRE:
                position = fin
            lignes.insert(position, ligne)
            fin += 1
    ecrire_texte(chemin, "\n".join(lignes))


def ajouter_suivi(chemin, texte):
    lignes = lire_texte(chemin).rstrip("\n").split("\n")
    debut, dans_code = None, False
    for i, ligne in enumerate(lignes):
        if est_cloture(ligne):
            dans_code = not dans_code
        elif not dans_code and est_titre_2(ligne) and ligne.lstrip("#").strip() == SECTION_SUIVI:
            debut = i
    if debut is None:
        lignes += ["", f"## {SECTION_SUIVI}", f"- {texte}"]
    else:
        fin, dans_code = len(lignes), False
        for i in range(debut + 1, len(lignes)):
            if est_cloture(lignes[i]):
                dans_code = not dans_code
            elif not dans_code and est_titre_2(lignes[i]):
                fin = i
                break
        while fin > debut + 1 and not lignes[fin - 1].strip():
            fin -= 1
        lignes.insert(fin, f"- {texte}")
    ecrire_texte(chemin, "\n".join(lignes))


def contenu_ticket(champs, resume):
    entete = "\n".join(
        f"{k}: {formater(champs[k])}" for k in ORDRE if champs.get(k) not in (None, "", [])
    )
    return (
        f"---\n{entete}\n---\n\n# {champs['cle']} · {champs['titre']}\n\n"
        f"## {SECTION_RESUME}\n{resume or ''}\n\n"
        f"## {SECTION_NOTES}\n{COMMENTAIRE_NOTES}\n\n"
        f"## {SECTION_SUIVI}\n- {champs['cree']} · créé\n"
    )


# ---------------------------------------------------------------- vérification

def verifier(backlog):
    """Retourne (erreurs, avertissements), chacun une liste de lignes."""
    erreurs = list(backlog.erreurs)
    avertissements = []
    vues = {}
    prefixe = backlog.prefixe
    for t in backlog.tickets:
        nom = t.chemin.name
        manquants = [c for c in OBLIGATOIRES if t.champs.get(c) in (None, "")]
        if manquants:
            erreurs.append(f"{nom} : champ(s) obligatoire(s) manquant(s) : {', '.join(manquants)}")
            continue
        if t.cle in vues:
            erreurs.append(f"{t.cle} : clé en double ({vues[t.cle]} et {nom})")
        vues[t.cle] = nom
        if prefixe and not re.fullmatch(rf"{re.escape(prefixe)}-\d+", t.cle):
            erreurs.append(f"{t.cle} : la clé doit être de la forme {prefixe}-<n>")
        if not (nom == f"{t.cle}.md" or nom.startswith(f"{t.cle}-")):
            erreurs.append(f"{t.cle} : le fichier {nom} doit commencer par « {t.cle}- »")
        if t.type not in TYPES:
            erreurs.append(f"{t.cle} : type « {t.type} » inconnu ({', '.join(TYPES)})")
        if t.statut not in STATUTS:
            erreurs.append(f"{t.cle} : statut « {t.statut} » inconnu ({', '.join(STATUTS)})")
        if not DATE.fullmatch(str(t.get("cree"))):
            erreurs.append(f"{t.cle} : cree doit être une date AAAA-MM-JJ")
        if t.champs.get("rang") is not None and t.rang is None:
            erreurs.append(f"{t.cle} : rang doit être un entier")
        if t.epic:
            epic = backlog.par_cle.get(t.epic)
            if t.type == "epic":
                erreurs.append(f"{t.cle} : une epic ne se range pas dans une autre epic")
            elif epic is None:
                erreurs.append(f"{t.cle} : epic {t.epic} introuvable")
            elif epic.type != "epic":
                erreurs.append(f"{t.cle} : {t.epic} n'est pas une epic")
        for autre in t.bloque_par:
            if autre not in backlog.par_cle:
                erreurs.append(f"{t.cle} : bloque_par cite {autre}, introuvable")
        fiche = backlog.chemin_fiche(t)
        if fiche and not fiche.is_file():
            avertissements.append(f"{t.cle} : fiche {t.get('fiche')} introuvable")
        if t.type == "story" and t.statut in STATUTS_AVEC_FICHE and not fiche:
            avertissements.append(f"{t.cle} : story « {STATUTS[t.statut]} » sans fiche")
        for nom_section in (SECTION_RESUME, SECTION_NOTES, SECTION_SUIVI):
            if section(t.corps, nom_section) is None:
                avertissements.append(f"{t.cle} : section « ## {nom_section} » absente")
        for note in t.notes():
            if not DATE.match(note):
                avertissements.append(f"{t.cle} : note « {note[:40]} » sans date en tête (AAAA-MM-JJ)")
        if t.get("jira") and not t.get("synchro_jira"):
            avertissements.append(f"{t.cle} : clé Jira sans date de synchro (kanban.py synchro)")
    return erreurs, avertissements


# ---------------------------------------------------------------- commandes

def tronquer(texte, largeur):
    return texte if len(texte) <= largeur else texte[: largeur - 1] + "…"


def cmd_init(args):
    dossier = args.dossier_resolu
    if (dossier / "config.yml").exists():
        raise ErreurBacklog(f"{dossier} contient déjà un backlog")
    prefixe = args.prefixe.upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,9}", prefixe):
        raise ErreurBacklog("le préfixe doit faire 2 à 10 lettres ou chiffres, en commençant par une lettre")
    (dossier / "tickets").mkdir(parents=True, exist_ok=True)
    ecrire_texte(dossier / "config.yml", "\n".join([
        "# Backlog local : la source de vérité des tickets. Voir README.md.",
        f"projet: {formater(args.projet)}",
        f"prefixe: {prefixe}",
        "# Jira (facultatif) : renseigné à la première synchronisation (skill kanban, references/jira.md).",
        "jira_site:",
        "jira_projet:",
        "# Documentation en lecture seule de « kanban serve » (/doc/) : dossiers depuis la racine du dépôt.",
        f"# documentation: {formater(list(DOCUMENTATION_PAR_DEFAUT))}   (valeur par défaut)",
    ]))
    modele = lire_texte(MODELE_README)
    ecrire_texte(dossier / "README.md",
                 modele.replace("{projet}", args.projet).replace("{prefixe}", prefixe))
    print(f"Backlog créé dans {dossier} : config.yml, README.md, tickets/")


def cmd_tableau(args):
    b = Backlog(args.dossier_resolu)
    tickets = b.tickets
    if args.epic:
        epic = b.trouver(args.epic)
        tickets = [t for t in tickets if t.epic == epic.cle or t.cle == epic.cle]
    gras = (lambda s: f"\033[1m{s}\033[0m") if sys.stdout.isatty() else (lambda s: s)
    print(f"{b.projet} · backlog ({b.relatif(b.dossier)}) · {len(tickets)} ticket(s)")
    for epic in sorted((t for t in b.tickets if t.type == "epic"), key=b.tri):
        if args.epic and epic.cle != args.epic.upper():
            continue
        enfants = b.enfants(epic)
        finis = sum(1 for t in enfants if t.statut == "termine")
        encours = [t.cle for t in enfants if t.statut in ("en-cadrage", "pret", "en-cours", "en-revue")]
        suite = f" · en cours : {', '.join(encours)}" if encours else ""
        print(f"  Epic {epic.cle} « {epic.titre} » : {finis}/{len(enfants)} terminé(s){suite}")
    largeur_cle = max((len(t.cle) for t in tickets), default=6)
    statuts = COLONNES + (["abandonne"] if args.tout else [])
    for statut in statuts:
        colonne = sorted((t for t in tickets if t.statut == statut), key=b.tri)
        print()
        print(gras(f"{STATUTS[statut].upper()} ({len(colonne)})"))
        for t in colonne:
            repere = b.tranche(t) or (TYPES.get(t.type, t.type).lower() if t.type != "story" else "")
            epic = b.par_cle.get(t.epic)
            extras = []
            if epic:
                extras.append(tronquer(epic.titre, 18))
            if t.notes():
                extras.append(f"{len(t.notes())} note(s)")
            if t.get("fiche"):
                extras.append("fiche")
            if t.bloque_par:
                extras.append("bloqué par " + ", ".join(t.bloque_par))
            if t.get("jira"):
                extras.append(f"Jira {t.get('jira')}")
            print(f"  {t.cle:<{largeur_cle}}  {repere:<6} {tronquer(t.titre, 52):<52}  {' · '.join(extras)}")
    for erreur in b.erreurs:
        print(f"! {erreur}", file=sys.stderr)


def cmd_verifier(args):
    b = Backlog(args.dossier_resolu)
    erreurs, avertissements = verifier(b)
    for ligne in erreurs:
        print(f"✗ {ligne}")
    for ligne in avertissements:
        print(f"! {ligne}")
    if erreurs:
        print(f"{len(erreurs)} erreur(s), {len(avertissements)} avertissement(s).")
        return 1
    print(f"✓ {len(b.tickets)} ticket(s), aucune erreur, {len(avertissements)} avertissement(s).")
    return 0


def cmd_nouveau(args):
    b = Backlog(args.dossier_resolu)
    if args.type not in TYPES:
        raise ErreurBacklog(f"type « {args.type} » inconnu ({', '.join(TYPES)})")
    if args.statut not in STATUTS:
        raise ErreurBacklog(f"statut « {args.statut} » inconnu ({', '.join(STATUTS)})")
    epic = None
    if args.epic:
        if args.type == "epic":
            raise ErreurBacklog("une epic ne se range pas dans une autre epic")
        epic = b.trouver(args.epic)
        if epic.type != "epic":
            raise ErreurBacklog(f"{epic.cle} n'est pas une epic")
    cle = b.prochaine_cle()
    champs = {
        "cle": cle, "titre": args.titre.strip(), "type": args.type, "statut": args.statut,
        "epic": epic.cle if epic else None, "rang": args.rang, "cree": aujourdhui(),
    }
    chemin = b.dossier / "tickets" / f"{cle}-{slug(args.titre)}.md"
    ecrire_texte(chemin, contenu_ticket(champs, args.resume))
    print(f"{cle} créé : {b.relatif(chemin)}")


def cmd_deplacer(args):
    b = Backlog(args.dossier_resolu)
    if args.statut not in STATUTS:
        raise ErreurBacklog(f"statut « {args.statut} » inconnu ({', '.join(STATUTS)})")
    t = b.trouver(args.cle)
    if t.statut == args.statut:
        print(f"{t.cle} est déjà « {STATUTS[args.statut]} ».")
        return 0
    ancien = t.statut
    modifier_champs(t.chemin, {"statut": args.statut})
    motif = f" · {args.motif}" if args.motif else ""
    ajouter_suivi(t.chemin, f"{aujourdhui()} · {ancien} → {args.statut}{motif}")
    print(f"{t.cle} : {STATUTS.get(ancien, ancien)} → {STATUTS[args.statut]}")
    if t.type == "story" and args.statut in STATUTS_AVEC_FICHE and not t.get("fiche"):
        print(f"! {t.cle} n'a pas de fiche (champ fiche).")
    return 0


def a_pousser(b):
    resultat = []
    for t in sorted(b.tickets, key=lambda t: (t.type != "epic", t.numero)):
        if not t.get("jira"):
            if t.statut != "abandonne":
                resultat.append(("creer", t))
        elif b.empreinte(t) != t.get("empreinte_jira"):
            resultat.append(("mettre-a-jour", t))
    return resultat


def cmd_a_pousser(args):
    b = Backlog(args.dossier_resolu)
    liste = a_pousser(b)
    if args.json:
        print(json.dumps([{
            "cle": t.cle, "action": action, "type": t.type, "statut": t.statut, "titre": t.titre,
            "jira": t.get("jira"), "epic": t.epic,
            "epic_jira": b.par_cle[t.epic].get("jira") if t.epic in b.par_cle else None,
            "bloque_par": t.bloque_par, "fichier": b.relatif(t.chemin),
            "fiche": t.get("fiche"),
        } for action, t in liste], ensure_ascii=False, indent=2))
        return 0
    if not (b.config.get("jira_site") and b.config.get("jira_projet")):
        print("Jira n'est pas encore configuré (config.yml : jira_site, jira_projet).")
    if not liste:
        print("Rien à pousser : Jira est à jour.")
        return 0
    libelles = {"creer": "à créer", "mettre-a-jour": "à mettre à jour"}
    reperes = [t.cle + (f" ({t.get('jira')})" if t.get("jira") else "") for _, t in liste]
    largeur = max(len(r) for r in reperes)
    for (action, t), repere in zip(liste, reperes):
        print(f"  {libelles[action]:<16} {repere:<{largeur}}  {STATUTS.get(t.statut, t.statut):<10}  {t.titre}")
    return 0


def cmd_synchro(args):
    b = Backlog(args.dossier_resolu)
    t = b.trouver(args.cle)
    maintenant = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    deja = t.get("jira")
    modifier_champs(t.chemin, {
        "jira": args.jira, "synchro_jira": maintenant, "empreinte_jira": b.empreinte(t),
    })
    ajouter_suivi(t.chemin, f"{aujourdhui()} · {'mis à jour dans' if deja else 'poussé dans'} Jira ({args.jira})")
    print(f"{t.cle} ↔ {args.jira} synchronisé ({maintenant}).")
    return 0


# ---------------------------------------------------------------- rendu Markdown

def echapper(texte):
    return html.escape(texte, quote=True)


def markdown_en_html(texte):
    """Le HTML d'un texte Markdown. Tout le texte est échappé : aucun HTML du fichier ne passe."""
    texte = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texte.replace("\r\n", "\n"))
    return "\n".join(blocs(sans_commentaires_html(texte.split("\n"))))


MD_COMMENTAIRE = re.compile(r"<!--.*?-->", re.DOTALL)


def sans_commentaires_html(lignes):
    """Les lignes sans leurs commentaires <!-- … -->, qui peuvent tenir sur plusieurs lignes, sauf dans le code."""
    sortie, texte, fin_du_code = [], [], None

    def vider_le_texte():
        if texte:
            sortie.extend(MD_COMMENTAIRE.sub("", "\n".join(texte)).split("\n"))
            texte.clear()

    for ligne in lignes:
        if fin_du_code:
            sortie.append(ligne)
            fin_du_code = None if fin_du_code.match(ligne) else fin_du_code
        elif MD_CLOTURE.match(ligne):
            vider_le_texte()
            sortie.append(ligne)
            fin_du_code = fin_de_code(ligne)
        else:
            texte.append(ligne)
    vider_le_texte()
    return sortie


def fin_de_code(ouverture):
    """La clôture d'un bloc de code : le même signe, au moins autant de fois."""
    cloture = MD_CLOTURE.match(ouverture).group(2)
    return re.compile(rf" {{0,3}}{re.escape(cloture[0])}{{{len(cloture)},}}[ \t]*$")


MD_TITRE = re.compile(r" {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
MD_ITEM = re.compile(r"( {0,3})([-*+]|\d{1,9}[.)])(?:( +)(.*))?$")
MD_CLOTURE = re.compile(r"( {0,3})(`{3,}|~{3,})(.*)$")
MD_DELIMITATION = re.compile(r" {0,3}\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
MD_CITATION = re.compile(r" {0,3}> ?(.*)$")
MD_FILET = re.compile(r" {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")


def blocs(lignes):
    """Le HTML de chaque bloc des lignes. Chaque lecteur de bloc rend (HTML, indice de la ligne suivante)."""
    sortie, i = [], 0
    while i < len(lignes):
        if not lignes[i].strip():
            i += 1
            continue
        bloc, i = lecteur_de_bloc(lignes, i)(lignes, i)
        sortie.append(bloc)
    return sortie


def lecteur_de_bloc(lignes, i):
    ligne = lignes[i]
    if MD_CLOTURE.match(ligne):
        return code
    if MD_TITRE.match(ligne):
        return titre
    if MD_FILET.match(ligne):  # avant les listes : « - - - » n'est pas une liste
        return filet
    if MD_ITEM.match(ligne):
        return liste
    if MD_CITATION.match(ligne):
        return citation
    if est_ligne_de_tableau(ligne) and i + 1 < len(lignes) and MD_DELIMITATION.match(lignes[i + 1]):
        return tableau
    return paragraphe


def filet(lignes, i):
    return "<hr>", i + 1


def citation(lignes, i):
    """Les lignes qui commencent par >. Elles gardent leurs retours à la ligne : une note de cadrage y cite
    une réponse mot pour mot."""
    interieur = []
    while i < len(lignes) and MD_CITATION.match(lignes[i]):
        texte = MD_CITATION.match(lignes[i]).group(1)
        interieur.append(texte + "  " if texte.strip() else texte)
        i += 1
    return "<blockquote>\n" + "\n".join(blocs(interieur)) + "\n</blockquote>", i


def est_ligne_de_tableau(ligne):
    return ligne.lstrip().startswith("|")


def tableau(lignes, i):
    """Un tableau : une ligne d'en-tête, une ligne de séparation |---|, puis les lignes qui commencent par |."""
    entete = "".join(f"<th>{en_ligne(c)}</th>" for c in cellules(lignes[i]))
    i += 2
    rangees = []
    while i < len(lignes) and est_ligne_de_tableau(lignes[i]):
        rangees.append("<tr>" + "".join(f"<td>{en_ligne(c)}</td>" for c in cellules(lignes[i])) + "</tr>")
        i += 1
    corps = "".join(f"{r}\n" for r in rangees)
    return f"<table>\n<thead>\n<tr>{entete}</tr>\n</thead>\n<tbody>\n{corps}</tbody>\n</table>", i


def cellules(ligne):
    """Les cellules d'une ligne de tableau. Une barre échappée (\\|) reste dans sa cellule, même dans du code."""
    interieur = ligne.strip()
    interieur = interieur[1:] if interieur.startswith("|") else interieur
    interieur = interieur[:-1] if re.search(r"(?<!\\)\|$", interieur) else interieur
    return [cellule.strip().replace("\\|", "|") for cellule in re.split(r"(?<!\\)\|", interieur)]


def code(lignes, i):
    """Un bloc de code délimité par ``` ou ~~~ : son texte tel quel, échappé, jusqu'à la clôture ou la fin."""
    info, fin = MD_CLOTURE.match(lignes[i]).group(3), fin_de_code(lignes[i])
    debut = i = i + 1
    while i < len(lignes) and not fin.match(lignes[i]):
        i += 1
    texte = "\n".join(lignes[debut:i])
    langage = info.split()[0].lower() if info.strip() else ""
    classe = f' class="language-{echapper(langage)}"' if langage else ""
    contenu = gherkin_en_html(texte) if langage in ("gherkin", "feature") else echapper(texte)
    return f"<pre><code{classe}>{contenu}</code></pre>", i + 1


# Mots-clés des étapes, avec l'espace ou l'apostrophe qui les suit (dictionnaire i18n de Gherkin, fr et en).
GHERKIN_ETAPES = [
    "Soit ", "Sachant que ", "Sachant qu'", "Sachant ",
    "Étant donné que ", "Étant donné qu'", "Étant donné ", "Étant donnée ", "Étant donnés ",
    "Étant données ", "Etant donné que ", "Etant donné qu'", "Etant donné ", "Etant donnée ",
    "Etant donnés ", "Etant données ",
    "Quand ", "Lorsque ", "Lorsqu'", "Alors ", "Donc ",
    "Et que ", "Et qu'", "Et ", "Mais que ", "Mais qu'", "Mais ",
    "Given ", "When ", "Then ", "And ", "But ", "* ",
]
GHERKIN_ETAPES += [mot[:-1] + "’" for mot in GHERKIN_ETAPES if mot.endswith("'")]
GHERKIN_BLOCS = [
    "Fonctionnalité", "Contexte", "Règle", "Scénario", "Plan du scénario", "Plan du Scénario",
    "Exemple", "Exemples",
    "Feature", "Background", "Rule", "Scenario", "Scenario Outline", "Scenario Template", "Example", "Examples",
    "Scenarios",
]


def alternatives(mots):
    """Une alternative d'expression régulière où le mot le plus long l'emporte (« Et qu' » avant « Et »)."""
    return "|".join(re.escape(mot) for mot in sorted(mots, key=len, reverse=True))


GHERKIN_ETAPE = re.compile(rf"(\s*)({alternatives(GHERKIN_ETAPES)})(.*)$")
GHERKIN_BLOC = re.compile(rf"(\s*)((?:{alternatives(GHERKIN_BLOCS)}):)(.*)$")


def gherkin_en_html(texte):
    """Le texte d'un bloc Gherkin, échappé, avec ses mots-clés mis en valeur ligne à ligne."""
    return "\n".join(ligne_gherkin(ligne) for ligne in texte.split("\n"))


def ligne_gherkin(ligne):
    commentaire = re.match(r"(\s*)(#.*)$", ligne)
    if commentaire:
        retrait, texte = commentaire.groups()
        return f'{retrait}<span class="gk-commentaire">{echapper(texte)}</span>'
    bloc = GHERKIN_BLOC.match(ligne)
    if bloc:
        retrait, mot, titre_du_bloc = bloc.groups()
        return (f'{retrait}<span class="gk-mot">{echapper(mot)}</span>'
                f'<span class="gk-titre">{avec_variables(titre_du_bloc)}</span>')
    etape = GHERKIN_ETAPE.match(ligne)
    if etape:
        retrait, mot, reste = etape.groups()
        espace = " " if mot.endswith(" ") else ""
        return f'{retrait}<span class="gk-mot">{echapper(mot.rstrip())}</span>{espace}{avec_variables(reste)}'
    return avec_variables(ligne)


def avec_variables(texte):
    """Le texte échappé, où les variables d'un plan du scénario (<niveaux choisis>) sont mises en valeur."""
    return re.sub(r"&lt;([^&]+?)&gt;", r'<span class="gk-variable">&lt;\1&gt;</span>', echapper(texte))


def liste(lignes, i):
    """Les items qui se suivent avec la même sorte de puce. Une ligne vide entre deux items, ou dans un item,
    aère la liste : ses paragraphes gardent leurs balises <p>."""
    balise, debut = balise_de_liste(MD_ITEM.match(lignes[i]).group(2))
    sorte, contenus, aeree = sorte_de_puce(lignes[i]), [], False
    while i < len(lignes) and sorte_de_puce(lignes[i]) == sorte:
        contenu, i = contenu_d_item(lignes, i)
        contenus.append(contenu)
        aeree = aeree or "" in contenu[1:]
        suivante = ligne_non_vide(lignes, i)
        if suivante < len(lignes) and sorte_de_puce(lignes[suivante]) == sorte:
            aeree, i = aeree or suivante > i, suivante
    items = "\n".join(item(contenu, aeree) for contenu in contenus)
    return f"<{balise}{debut}>\n{items}\n</{balise}>", i


def balise_de_liste(puce):
    """La balise d'une liste et, pour une liste numérotée qui ne commence pas à 1, son attribut start."""
    if not puce[0].isdigit():
        return "ul", ""
    numero = int(puce[:-1])
    return "ol", "" if numero == 1 else f' start="{numero}"'


def item(contenu, aeree):
    parties = blocs(contenu)
    return "<li>" + "\n".join(parties if aeree else map(sans_paragraphe, parties)) + "</li>"


def ligne_non_vide(lignes, i):
    while i < len(lignes) and not lignes[i].strip():
        i += 1
    return i


def sorte_de_puce(ligne):
    """« - », « * », « + », « . » ou « ) », None hors d'un item : une autre sorte commence une autre liste."""
    puce = MD_ITEM.match(ligne)
    if not puce:
        return None
    return puce.group(2)[-1] if puce.group(2)[0].isdigit() else puce.group(2)


def contenu_d_item(lignes, i):
    """Les lignes d'un item, sans sa puce ni le retrait de son contenu : une liste imbriquée y reste une liste."""
    retrait, puce, espaces, texte = MD_ITEM.match(lignes[i]).groups()
    colonne = len(retrait) + len(puce) + len(espaces or " ")
    contenu = [texte or ""]
    i += 1
    while i < len(lignes):
        if not lignes[i].strip():
            suivante = ligne_non_vide(lignes, i)
            if suivante == len(lignes) or retrait_de(lignes[suivante]) < colonne:
                break
            contenu += [""] * (suivante - i)
            i = suivante
        if retrait_de(lignes[i]) >= colonne:
            contenu.append(lignes[i][colonne:])
        elif lecteur_de_bloc(lignes, i) is paragraphe:
            contenu.append(lignes[i].strip())  # continuation sans retrait du paragraphe de l'item
        else:
            break
        i += 1
    return contenu, i


def retrait_de(ligne):
    return len(ligne) - len(ligne.lstrip(" "))


def sans_paragraphe(bloc):
    """Le texte d'un paragraphe d'item, sans ses balises <p> : la liste est serrée."""
    return bloc[3:-4] if bloc.startswith("<p>") and bloc.endswith("</p>") else bloc


def titre(lignes, i):
    dieses, texte = MD_TITRE.match(lignes[i]).groups()
    return f"<h{len(dieses)}>{en_ligne(texte or '')}</h{len(dieses)}>", i + 1


def paragraphe(lignes, i):
    debut = i
    i += 1
    while i < len(lignes) and lignes[i].strip() and lecteur_de_bloc(lignes, i) is paragraphe:
        i += 1
    *premieres, derniere = lignes[debut:i]
    rendu = [ligne_suivie_d_une_autre(ligne) for ligne in premieres] + [en_ligne(derniere.strip())]
    return "<p>" + "\n".join(rendu) + "</p>", i


MD_RETOUR_FORCE = re.compile(r"(?:  +|\\)$")


def ligne_suivie_d_une_autre(ligne):
    """Deux espaces ou un antislash en fin de ligne forcent le retour à la ligne."""
    texte = ligne.lstrip()
    if MD_RETOUR_FORCE.search(texte):
        return en_ligne(MD_RETOUR_FORCE.sub("", texte).rstrip()) + "<br>"
    return en_ligne(texte.rstrip())


MD_GRAS = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
# Un souligné au milieu d'un mot (synchro_jira) n'ouvre ni ne ferme l'italique.
MD_ITALIQUE = re.compile(r"(?<!\*)\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?!\*)|(?<!\w)_(?=[^\s_])(.+?)(?<=[^\s_])_(?!\w)")
MD_LIEN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
MIS_DE_COTE = re.compile("\x00(\\d+)\x00")
PONCTUATION = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"


def en_ligne(texte):
    """Le HTML d'une ligne de texte : code en ligne, liens, gras et italique, le reste échappé.

    Le code et les caractères échappés par un antislash sont rendus d'abord et mis de côté
    (repère \\x00n\\x00) : la mise en forme ne les atteint pas.
    """
    de_cote = []

    def mettre_de_cote(fragment):
        de_cote.append(fragment)
        return f"\x00{len(de_cote) - 1}\x00"

    texte = code_et_echappements(texte, mettre_de_cote)
    texte = MD_LIEN.sub(lambda m: lien(m.group(1), m.group(2)), echapper(texte))
    texte = MD_GRAS.sub(r"<strong>\1</strong>", texte)
    texte = MD_ITALIQUE.sub(lambda m: f"<em>{m.group(1) or m.group(2)}</em>", texte)
    return MIS_DE_COTE.sub(lambda m: de_cote[int(m.group(1))], texte)


def code_et_echappements(texte, mettre_de_cote):
    """Lu de gauche à droite : un antislash échappe un backtick, mais n'échappe rien dans le code."""
    morceaux, i = [], 0
    while i < len(texte):
        if texte[i] == "\\" and i + 1 < len(texte) and texte[i + 1] in PONCTUATION:
            morceaux.append(mettre_de_cote(echapper(texte[i + 1])))
            i += 2
        elif texte[i] == "`":
            ouverture = re.match(r"`+", texte[i:]).group(0)
            fermeture = re.compile(rf"(?<!`){ouverture}(?!`)").search(texte, i + len(ouverture))
            if fermeture:
                code = texte[i + len(ouverture):fermeture.start()]
                morceaux.append(mettre_de_cote(f"<code>{echapper(code)}</code>"))
                i = fermeture.end()
            else:
                morceaux.append(ouverture)
                i += len(ouverture)
        else:
            morceaux.append(texte[i])
            i += 1
    return "".join(morceaux)


def lien(texte, url):
    """Un lien dont le texte et l'url sont déjà échappés. Un autre site s'ouvre dans un autre onglet.

    Seuls les liens relatifs, http, https et mailto en sont : les autres schémas (javascript:, data:…)
    pourraient exécuter du code, et une url qui contient du code mis de côté n'en est pas une.
    """
    schema = re.match(r"([a-zA-Z][a-zA-Z0-9+.-]*):", url)
    if "\x00" in url or (schema and schema.group(1).lower() not in ("http", "https", "mailto")):
        return texte
    if re.match(r"https?://", url, re.IGNORECASE):
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{texte}</a>'
    return f'<a href="{url}">{texte}</a>'


# ---------------------------------------------------------------- tableau HTML

def donnees_html(b, live):
    documentation = b.documentation() if live else None
    tickets = []
    for t in b.tickets:
        fiche = b.chemin_fiche(t)
        epic = b.par_cle.get(t.epic)
        tickets.append({
            "cle": t.cle, "titre": t.titre, "type": t.type, "statut": t.statut,
            "epic": t.epic, "epicTitre": epic.titre if epic else None, "epicNumero": epic.numero if epic else None,
            "rang": t.rang, "numero": t.numero, "tranche": b.tranche(t),
            "fiche": t.get("fiche"), "jira": t.get("jira"), "bloquePar": t.bloque_par,
            "notes": len(t.notes()), "derniereNote": t.derniere_note(), "cree": t.get("cree"),
            "fichier": b.relatif(t.chemin), "corps": t.corps,
            # Le titre du ticket est déjà en tête du panneau.
            "corpsHtml": markdown_en_html(re.sub(r"^\s*# .*\n", "", t.corps, count=1)),
            "ficheHtml": markdown_en_html(lire_texte(fiche)) if fiche and fiche.is_file() else None,
            "ficheUrl": url_de_fiche(documentation, t) if documentation else None,
        })
    return {
        "projet": b.projet, "dossier": b.relatif(b.dossier),
        "genere": dt.datetime.now().strftime("%d/%m/%Y %H:%M"), "live": live,
        "etat": b.etat() if live else None, "erreurs": b.erreurs,
        "documentation": "/doc/" if live else None,
        "statuts": [{"id": k, "libelle": v} for k, v in STATUTS.items()], "types": TYPES,
        "tickets": tickets,
    }


def url_de_fiche(documentation, ticket):
    """L'adresse de la page de la fiche d'un ticket, si la documentation la sert."""
    fiche = ticket.get("fiche")
    if not fiche or documentation.document(str(fiche)) is None:
        return None
    return url_de_page(Path(str(fiche)).as_posix())


def generer_html(b, live=False):
    donnees = json.dumps(donnees_html(b, live), ensure_ascii=False).replace("<", "\\u003c")
    titre = f"{b.projet} · backlog"
    return (MODELE_HTML.replace("__TITRE__", titre.replace("&", "&amp;").replace("<", "&lt;"))
            .replace("__DONNEES__", donnees))


def cmd_html(args):
    b = Backlog(args.dossier_resolu)
    sortie = Path(args.sortie) if args.sortie else Path(tempfile.gettempdir()) / f"kanban-{slug(b.projet)}.html"
    sortie.write_text(generer_html(b), encoding="utf-8")
    print(f"Tableau écrit dans {sortie}")
    if not args.pas_ouvrir:
        webbrowser.open(sortie.resolve().as_uri())
    return 0


# ---------------------------------------------------------------- pages de documentation

def url_de_page(chemin):
    """L'adresse d'une page de documentation : son chemin depuis la racine du dépôt, sous /doc/. Un lien
    relatif d'une page vers une autre (glossaire.md, ../specs/x.md) y mène donc sans être réécrit."""
    return "/doc/" + urllib.parse.quote(chemin)


def page_sommaire(b):
    documentation = b.documentation()
    rubriques = "\n".join(rubrique_html(rubrique) for rubrique in documentation.sommaire())
    entete = (f'<nav class="fil"><a href="/">Tableau</a> › Documentation</nav>\n'
              f"<h1>Documentation de {echapper(b.projet)}</h1>")
    return page_html(f"{b.projet} · documentation", f"{entete}\n{rubriques}", documentation.etat())


def page_document(b, chemin):
    """La page d'un document de la documentation, ou None s'il n'est pas à servir."""
    documentation = b.documentation()
    fichier = documentation.document(chemin)
    if fichier is None:
        return None
    texte = lire_texte(fichier)
    entete = (f'<nav class="fil"><a href="/">Tableau</a> › <a href="/doc/">Documentation</a> › '
              f'<span class="chemin">{echapper(chemin)}</span></nav>')
    contenu = f'<article class="md">\n{markdown_en_html(texte)}\n</article>'
    return page_html(f"{titre_de_page(texte, fichier.name)} · {b.projet}",
                     entete + tickets_de_la_fiche(b, fichier) + f"\n{contenu}", documentation.etat())


def tickets_de_la_fiche(b, fichier):
    """Les tickets dont le champ fiche désigne ce fichier, avec un lien vers chacun sur le tableau."""
    tickets = [t for t in b.tickets if b.chemin_fiche(t) and b.chemin_fiche(t).resolve() == fichier.resolve()]
    if not tickets:
        return ""
    liens = ", ".join(f'<a href="/#{echapper(t.cle)}">{echapper(t.cle)} · {echapper(t.titre)}</a>'
                      for t in tickets)
    return f'\n<p class="sous">Fiche de {liens}</p>'


def rubrique_html(rubrique):
    entete = f'<section class="rubrique"><h2>{echapper(rubrique.dossier)}</h2>'
    if not rubrique.existe:
        absent = f"le dossier {echapper(rubrique.dossier)} n’existe pas"
        return f'{entete}<p class="vide">Aucune page pour l’instant : {absent}.</p></section>'
    if not rubrique.pages:
        return f'{entete}<p class="vide">Aucune page pour l’instant.</p></section>'
    return f'{entete}<ul>{"".join(map(lien_de_page, rubrique.pages))}</ul></section>'


def lien_de_page(page):
    entree = ' <span class="badge">point d’entrée</span>' if page.est_point_d_entree else ""
    return f'<li><a href="{echapper(url_de_page(page.chemin))}">{echapper(page.titre)}</a>{entree}</li>'


def page_html(titre, corps, etat):
    """Une page de documentation, qui se recharge quand l'empreinte de la documentation n'est plus etat.
    Les repères du modèle sont remplacés en une passe : un texte qui en contient un reste tel quel."""
    valeurs = {"TITRE": echapper(titre), "ETAT": json.dumps(etat), "CORPS": corps}
    return re.sub(r"__(TITRE|ETAT|CORPS)__", lambda m: valeurs[m.group(1)], MODELE_PAGE)


HTML = "text/html; charset=utf-8"
TEXTE = "text/plain; charset=utf-8"


def reponse(dossier, cible):
    """(code HTTP, type de contenu, corps) d'un GET de « serve ». Le corps d'une erreur est son message."""
    chemin = cible.split("?")[0]
    try:
        b = Backlog(dossier)
        if chemin == "/":
            return 200, HTML, generer_html(b, live=True)
        if chemin == "/etat":
            return 200, TEXTE, b.etat()
        if chemin == "/etat/documentation":
            return 200, TEXTE, b.documentation().etat()
        if chemin in ("/doc", "/doc/"):
            return 200, HTML, page_sommaire(b)
        if chemin.startswith("/doc/"):
            page = page_document(b, urllib.parse.unquote(chemin[len("/doc/"):]))
            return (200, HTML, page) if page else (404, None, "Document introuvable")
        return 404, None, None
    except ErreurBacklog as exc:
        return 200, TEXTE, f"Erreur : {exc}"


def cmd_serve(args):
    dossier = args.dossier_resolu
    Backlog(dossier)  # échoue tout de suite s'il n'y a pas de backlog

    class Gestionnaire(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            code, type_, corps = reponse(dossier, self.path)
            if code != 200:
                self.send_error(code, corps)
                return
            donnees = corps.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", type_)
            self.send_header("Content-Length", str(len(donnees)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(donnees)

        def log_message(self, *_):
            pass

    serveur = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Gestionnaire)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Tableau en direct sur {url} et documentation sur {url}doc/ (Ctrl+C pour arrêter). "
          "Ils se rechargent quand un fichier change.", flush=True)
    if not args.pas_ouvrir:
        webbrowser.open(url)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print()
    return 0


# Les couleurs, le thème sombre et le rendu Markdown (.md), communs au tableau et aux pages de documentation.
STYLE_COMMUN = r""":root {
  --bg: #f5f6f8; --surface: #ffffff; --colonne: #ebedf1; --text: #1c2230; --muted: #626b7d;
  --border: #dde1e7; --accent: #3558d6; --chip: #eef0f4; --alerte-bg: #fff3e0; --alerte: #8a4a00;
  --epic: #7048e8; --story: #2b8a3e; --tache: #1971c2; --spike: #d9480f; --bug: #c92a2a;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #121418; --surface: #1c1f26; --colonne: #171a20; --text: #e4e7ec; --muted: #98a1b0;
    --border: #2b303a; --accent: #8aa4ff; --chip: #262a33; --alerte-bg: #3a2a12; --alerte: #ffc078;
    --epic: #9775fa; --story: #51cf66; --tache: #4dabf7; --spike: #ff922b; --bug: #ff6b6b;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif; }
.sous { color: var(--muted); font-size: 12px; }
.live { color: var(--story); }
.chemin { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11.5px; }
.badge { padding: 0 6px; border-radius: 10px; background: var(--chip); font-size: 11px; white-space: nowrap; }
.md { overflow-wrap: anywhere; }
.md h1 { font-size: 19px; margin: 12px 0 8px; }
.md h2 { font-size: 15px; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 1px solid var(--border); }
.md h3 { font-size: 14px; margin: 18px 0 6px; }
.md p { margin: 6px 0; }
.md ul, .md ol { margin: 4px 0; padding-left: 22px; }
.md blockquote { margin: 6px 0; padding: 4px 12px; border-left: 3px solid var(--accent);
  background: var(--chip); border-radius: 0 6px 6px 0; }
.md pre { background: var(--chip); padding: 10px 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; }
.md code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12.5px; }
.md :not(pre) > code { background: var(--chip); padding: 0 4px; border-radius: 4px; }
.md table { border-collapse: collapse; font-size: 13px; margin: 8px 0; display: block; overflow-x: auto; }
.md th, .md td { border: 1px solid var(--border); padding: 4px 8px; vertical-align: top; text-align: left; }
.md a { color: var(--accent); }
.md hr { border: 0; border-top: 1px solid var(--border); margin: 16px 0; }
.md code.language-gherkin { white-space: pre-wrap; }
.gk-mot { color: var(--accent); font-weight: 600; }
.gk-titre { font-weight: 600; }
.gk-variable { color: var(--spike); }
.gk-commentaire { color: var(--muted); font-style: italic; }"""


MODELE_HTML = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITRE__</title>
<style>
__STYLE_COMMUN__
header { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; padding: 16px 20px 6px; }
h1 { font-size: 18px; margin: 0; }
.filtres { margin-left: auto; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
select, input[type=search] { font: inherit; padding: 5px 8px; border: 1px solid var(--border);
  border-radius: 6px; background: var(--surface); color: var(--text); }
label.case { font-size: 13px; color: var(--muted); display: flex; gap: 4px; align-items: center; }
.epics { display: flex; flex-wrap: wrap; gap: 8px 24px; padding: 4px 20px 10px; }
.epic-prog { font-size: 12px; color: var(--muted); min-width: 220px; cursor: pointer; }
.epic-prog b { color: var(--text); font-weight: 600; }
.barre { height: 4px; background: var(--chip); border-radius: 2px; overflow: hidden; margin-top: 4px; }
.barre span { display: block; height: 100%; background: var(--story); }
.alerte { margin: 0 20px 10px; padding: 8px 12px; border-radius: 6px; background: var(--alerte-bg);
  color: var(--alerte); font-size: 13px; }
main { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(180px, 1fr); gap: 10px;
  padding: 4px 20px 24px; overflow-x: auto; align-items: start; }
.colonne { background: var(--colonne); border-radius: 10px; padding: 8px; min-height: 120px; }
.colonne h2 { display: flex; justify-content: space-between; margin: 4px 4px 8px; font-size: 12px;
  font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: var(--muted); }
.vide { color: var(--muted); text-align: center; margin: 16px 0; }
.carte { display: block; width: 100%; text-align: left; font: inherit; color: inherit; cursor: pointer;
  background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--story);
  border-radius: 8px; padding: 8px 10px; margin: 0 0 8px; }
.carte:hover, .carte:focus-visible { border-color: var(--accent); outline: none; }
.t-epic { border-left-color: var(--epic); } .t-tache { border-left-color: var(--tache); }
.t-spike { border-left-color: var(--spike); } .t-bug { border-left-color: var(--bug); }
.haut, .bas { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: 12px; color: var(--muted); }
.carte .titre { margin: 4px 0; font-weight: 500; }
.cle { font-weight: 600; font-size: 12px; font-variant-numeric: tabular-nums; letter-spacing: .02em; }
aside { position: fixed; top: 0; right: 0; bottom: 0; width: min(760px, 100%); background: var(--surface);
  border-left: 1px solid var(--border); box-shadow: -8px 0 24px rgba(0,0,0,.12); overflow-y: auto;
  transform: translateX(105%); transition: transform .18s ease; padding: 18px 24px 40px; }
aside.ouvert { transform: none; }
.panneau-haut { display: flex; justify-content: space-between; align-items: start; gap: 12px; }
.fermer { font: inherit; font-size: 20px; line-height: 1; border: 0; background: none; color: var(--muted); cursor: pointer; }
.meta { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 12px; color: var(--muted); margin: 8px 0 12px; }
.meta a, .sous a { color: var(--accent); cursor: pointer; }
.onglets { display: flex; gap: 4px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
.onglets button { font: inherit; font-size: 13px; padding: 6px 10px; border: 0; background: none;
  color: var(--muted); border-bottom: 2px solid transparent; cursor: pointer; }
.onglets button.actif { color: var(--text); border-bottom-color: var(--accent); }
@media (max-width: 700px) {
  header, .epics { padding-left: 16px; padding-right: 16px; }
  main { grid-auto-flow: row; grid-auto-columns: auto; padding: 4px 16px 24px; }
  .filtres { margin-left: 0; }
  aside { padding: 14px 16px 32px; }
}
</style>
</head>
<body>
<header>
  <div>
    <h1 id="titre"></h1>
    <div class="sous" id="sous"></div>
  </div>
  <div class="filtres">
    <select id="filtre-epic" aria-label="Epic"></select>
    <input type="search" id="filtre-texte" placeholder="Rechercher…" aria-label="Rechercher">
    <label class="case"><input type="checkbox" id="filtre-abandonnes"> Abandonnés</label>
  </div>
</header>
<div class="epics" id="epics"></div>
<div id="alertes"></div>
<main id="tableau"></main>
<aside id="panneau" aria-hidden="true"></aside>
<script type="application/json" id="donnees">__DONNEES__</script>
<script>
const D = JSON.parse(document.getElementById("donnees").textContent);
const $ = (s) => document.querySelector(s);
const parCle = Object.fromEntries(D.tickets.map((t) => [t.cle, t]));
const libelle = Object.fromEntries(D.statuts.map((s) => [s.id, s.libelle]));
const filtres = { epic: "", texte: "", abandonnes: false };
try { Object.assign(filtres, JSON.parse(sessionStorage.getItem("kanban-filtres") || "{}")); } catch (e) {}
const sauver = () => { try { sessionStorage.setItem("kanban-filtres", JSON.stringify(filtres)); } catch (e) {} };

function esc(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function tri(a, b) {
  const groupe = (t) => t.epicNumero ?? (t.type === "epic" ? t.numero : 1e9);
  const rang = (t) => (t.type === "epic" ? -1 : t.rang ?? 1e6);
  return groupe(a) - groupe(b) || rang(a) - rang(b) || a.numero - b.numero;
}
function visible(t) {
  if (filtres.epic === "-" && (t.epic || t.type === "epic")) return false;
  if (filtres.epic && filtres.epic !== "-" && t.epic !== filtres.epic && t.cle !== filtres.epic) return false;
  if (filtres.texte) {
    const q = filtres.texte.toLowerCase();
    if (!(t.cle + " " + t.titre + " " + t.corps).toLowerCase().includes(q)) return false;
  }
  return true;
}
function carte(t) {
  const haut = ['<span class="cle">' + esc(t.cle) + "</span>"];
  if (t.tranche) haut.push('<span class="badge">' + esc(t.tranche) + "</span>");
  else if (t.type !== "story") haut.push('<span class="badge">' + esc(D.types[t.type] || t.type) + "</span>");
  const bas = [];
  if (t.epicTitre) bas.push(esc(t.epicTitre));
  if (t.type === "epic") {
    const enfants = D.tickets.filter((e) => e.epic === t.cle && e.statut !== "abandonne");
    bas.push(enfants.filter((e) => e.statut === "termine").length + "/" + enfants.length + " terminés");
  }
  if (t.notes) bas.push("✎ " + t.notes + (t.notes > 1 ? " notes" : " note"));
  if (t.fiche) bas.push("fiche");
  if (t.bloquePar.length) bas.push("bloqué par " + esc(t.bloquePar.join(", ")));
  if (t.jira) bas.push("Jira " + esc(t.jira));
  return '<button class="carte t-' + esc(t.type) + '" data-cle="' + esc(t.cle) + '">'
    + '<div class="haut">' + haut.join("") + "</div>"
    + '<div class="titre">' + esc(t.titre) + "</div>"
    + (bas.length ? '<div class="bas">' + bas.join(" · ") + "</div>" : "") + "</button>";
}
function rendre() {
  const statuts = D.statuts.filter((s) => s.id !== "abandonne" || filtres.abandonnes);
  $("#tableau").innerHTML = statuts.map((s) => {
    const ts = D.tickets.filter((t) => t.statut === s.id && visible(t)).sort(tri);
    return '<section class="colonne"><h2><span>' + esc(s.libelle) + "</span><span>" + ts.length + "</span></h2>"
      + (ts.map(carte).join("") || '<p class="vide">—</p>') + "</section>";
  }).join("");
}
function enTete() {
  $("#titre").textContent = D.projet + " · backlog";
  $("#sous").innerHTML = esc(D.dossier) + " · " + D.tickets.length + " tickets · généré le " + esc(D.genere)
    + (D.live ? ' · <span class="live">● en direct</span>' : "")
    + (D.documentation ? ' · <a href="' + esc(D.documentation) + '">Documentation</a>' : "");
  const epics = D.tickets.filter((t) => t.type === "epic").sort(tri);
  $("#filtre-epic").innerHTML = '<option value="">Toutes les epics</option>'
    + epics.map((e) => '<option value="' + esc(e.cle) + '">' + esc(e.cle + " · " + e.titre) + "</option>").join("")
    + '<option value="-">Sans epic</option>';
  $("#filtre-epic").value = filtres.epic;
  $("#filtre-texte").value = filtres.texte;
  $("#filtre-abandonnes").checked = filtres.abandonnes;
  $("#epics").innerHTML = epics.map((e) => {
    const enfants = D.tickets.filter((t) => t.epic === e.cle && t.statut !== "abandonne");
    const finis = enfants.filter((t) => t.statut === "termine").length;
    const part = enfants.length ? Math.round((100 * finis) / enfants.length) : 0;
    return '<div class="epic-prog" data-epic="' + esc(e.cle) + '"><b>' + esc(e.titre) + "</b> · " + finis + "/" + enfants.length
      + ' terminés<div class="barre"><span style="width:' + part + '%"></span></div></div>';
  }).join("");
  $("#alertes").innerHTML = D.erreurs.length
    ? '<div class="alerte">Tickets illisibles : ' + D.erreurs.map(esc).join(" · ") + "</div>" : "";
}
function ouvrir(cle, onglet) {
  const t = parCle[cle];
  if (!t) return;
  const meta = [esc(D.types[t.type] || t.type), esc(libelle[t.statut] || t.statut)];
  if (t.epic) meta.push('Epic <a data-ouvrir="' + esc(t.epic) + '">' + esc(t.epic + " · " + (t.epicTitre || "")) + "</a>");
  if (t.tranche) meta.push("Tranche " + esc(t.tranche.slice(1)));
  if (t.bloquePar.length) meta.push("Bloqué par " + t.bloquePar.map((c) => '<a data-ouvrir="' + esc(c) + '">' + esc(c) + "</a>").join(", "));
  if (t.ficheUrl) meta.push('<a href="' + esc(t.ficheUrl) + '">Page de la fiche</a>');
  meta.push(t.jira ? "Jira " + esc(t.jira) : "pas dans Jira");
  meta.push("créé le " + esc(t.cree));
  meta.push('<span class="chemin">' + esc(t.fichier) + "</span>");
  const aFiche = !!t.ficheHtml;
  const vue = onglet === "fiche" && aFiche ? "fiche" : "ticket";
  const p = $("#panneau");
  p.innerHTML = '<div class="panneau-haut"><div><span class="cle">' + esc(t.cle) + "</span><h1 style=\"margin:4px 0 0;font-size:18px\">"
    + esc(t.titre) + '</h1></div><button class="fermer" aria-label="Fermer">×</button></div>'
    + '<div class="meta">' + meta.join("<span>·</span>") + "</div>"
    + '<div class="onglets"><button data-onglet="ticket" class="' + (vue === "ticket" ? "actif" : "") + '">Ticket</button>'
    + (aFiche ? '<button data-onglet="fiche" class="' + (vue === "fiche" ? "actif" : "") + '">Fiche · ' + esc(t.fiche) + "</button>"
      : (t.fiche ? '<button disabled title="Fichier introuvable">Fiche introuvable</button>' : ""))
    + "</div>"
    + '<div class="md">' + (vue === "fiche" ? t.ficheHtml : t.corpsHtml) + "</div>";
  p.classList.add("ouvert");
  p.setAttribute("aria-hidden", "false");
  p.scrollTop = 0;
  history.replaceState(null, "", "#" + cle + (vue === "fiche" ? "/fiche" : ""));
}
function fermer() {
  $("#panneau").classList.remove("ouvert");
  $("#panneau").setAttribute("aria-hidden", "true");
  history.replaceState(null, "", location.pathname + location.search);
}

document.addEventListener("click", (ev) => {
  const c = ev.target.closest(".carte");
  if (c) return ouvrir(c.dataset.cle);
  const lien = ev.target.closest("[data-ouvrir]");
  if (lien) return ouvrir(lien.dataset.ouvrir);
  const onglet = ev.target.closest("[data-onglet]");
  if (onglet) return ouvrir(location.hash.slice(1).split("/")[0], onglet.dataset.onglet);
  if (ev.target.closest(".fermer")) return fermer();
  const epic = ev.target.closest("[data-epic]");
  if (epic) { filtres.epic = filtres.epic === epic.dataset.epic ? "" : epic.dataset.epic; sauver(); enTete(); rendre(); }
});
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") fermer(); });
$("#filtre-epic").addEventListener("change", (ev) => { filtres.epic = ev.target.value; sauver(); rendre(); });
$("#filtre-texte").addEventListener("input", (ev) => { filtres.texte = ev.target.value; sauver(); rendre(); });
$("#filtre-abandonnes").addEventListener("change", (ev) => { filtres.abandonnes = ev.target.checked; sauver(); rendre(); });

enTete();
rendre();
if (location.hash.length > 1) {
  const [cle, onglet] = decodeURIComponent(location.hash.slice(1)).split("/");
  ouvrir(cle, onglet);
}
if (D.live) {
  setInterval(async () => {
    try {
      const r = await fetch("/etat", { cache: "no-store" });
      if (r.ok && (await r.text()) !== D.etat) location.reload();
    } catch (e) { /* serveur arrêté : on garde la dernière vue */ }
  }, 2000);
}
</script>
</body>
</html>
""".replace("__STYLE_COMMUN__", STYLE_COMMUN)


MODELE_PAGE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITRE__</title>
<style>
__STYLE_COMMUN__
.page { max-width: 920px; margin: 0 auto; padding: 16px 20px 48px; }
.fil { font-size: 13px; color: var(--muted); }
.fil a, .page > .sous a, .rubrique a { color: var(--accent); text-decoration: none; }
.fil a:hover, .page > .sous a:hover, .rubrique a:hover { text-decoration: underline; }
.page > h1 { font-size: 20px; margin: 14px 0 4px; }
.page > .sous { margin: 6px 0 0; font-size: 13px; }
.page > .md { font-size: 15px; line-height: 1.55; margin-top: 4px; }
.page > .md h1 { font-size: 22px; }
.page > .md pre { font-size: 13px; }
.rubrique h2 { font-size: 15px; margin: 24px 0 6px; }
.rubrique ul { list-style: none; padding: 0; margin: 0; }
.rubrique li { display: flex; flex-wrap: wrap; gap: 4px 10px; align-items: baseline; padding: 6px 0;
  border-bottom: 1px solid var(--border); }
.rubrique a { font-weight: 500; }
.vide { color: var(--muted); }
@media (max-width: 700px) { .page { padding: 12px 16px 40px; } }
</style>
</head>
<body>
<div class="page">
__CORPS__
</div>
<script>
const etat = __ETAT__;
setInterval(async () => {
  try {
    const r = await fetch("/etat/documentation", { cache: "no-store" });
    if (r.ok && (await r.text()) !== etat) location.reload();
  } catch (e) { /* serveur arrêté : on garde la dernière vue */ }
}, 2000);
</script>
</body>
</html>
""".replace("__STYLE_COMMUN__", STYLE_COMMUN)


# ---------------------------------------------------------------- entrée

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="kanban.py", description="Backlog local en Markdown, façon Jira.")
    parser.add_argument("--dossier", help="dossier du backlog (défaut : docs/backlog du dépôt git)")
    sous = parser.add_subparsers(dest="commande")

    p = sous.add_parser("init", help="amorcer un backlog dans le dépôt")
    p.add_argument("--projet", required=True)
    p.add_argument("--prefixe", required=True, help="préfixe des clés, ex. BOU")
    p.set_defaults(fonction=cmd_init)

    p = sous.add_parser("tableau", help="afficher le tableau dans le terminal")
    p.add_argument("--epic", help="seulement cette epic et ses tickets")
    p.add_argument("--tout", action="store_true", help="avec les tickets abandonnés")
    p.set_defaults(fonction=cmd_tableau)

    p = sous.add_parser("html", help="écrire le tableau dans un fichier HTML et l'ouvrir")
    p.add_argument("--sortie", help="fichier à écrire (défaut : dossier temporaire)")
    p.add_argument("--pas-ouvrir", action="store_true")
    p.set_defaults(fonction=cmd_html)

    p = sous.add_parser("serve", help="servir le tableau et la documentation (/doc/) en direct sur 127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--pas-ouvrir", action="store_true")
    p.set_defaults(fonction=cmd_serve)

    p = sous.add_parser("verifier", help="vérifier les tickets (code de sortie 1 en cas d'erreur)")
    p.set_defaults(fonction=cmd_verifier)

    p = sous.add_parser("nouveau", help="créer un ticket avec la clé suivante")
    p.add_argument("titre")
    p.add_argument("--type", default="story", help=", ".join(TYPES))
    p.add_argument("--epic")
    p.add_argument("--rang", type=int)
    p.add_argument("--statut", default="a-cadrer", help=", ".join(STATUTS))
    p.add_argument("--resume", help="le besoin en une ou deux phrases")
    p.set_defaults(fonction=cmd_nouveau)

    p = sous.add_parser("deplacer", help="changer le statut d'un ticket et le noter dans son suivi")
    p.add_argument("cle")
    p.add_argument("statut", help=", ".join(STATUTS))
    p.add_argument("--motif")
    p.set_defaults(fonction=cmd_deplacer)

    p = sous.add_parser("a-pousser", help="lister les tickets à créer ou à mettre à jour dans Jira")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fonction=cmd_a_pousser)

    p = sous.add_parser("synchro", help="noter qu'un ticket vient d'être poussé dans Jira")
    p.add_argument("cle")
    p.add_argument("--jira", required=True, help="clé du ticket dans Jira, ex. BOUTIQUE-12")
    p.set_defaults(fonction=cmd_synchro)

    args = parser.parse_args(argv)
    if not args.commande:
        args = parser.parse_args([*(argv or sys.argv[1:]), "tableau"])
    args.dossier_resolu = Path(args.dossier).expanduser().resolve() if args.dossier else dossier_par_defaut()
    try:
        return args.fonction(args) or 0
    except ErreurBacklog as exc:
        print(f"kanban : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

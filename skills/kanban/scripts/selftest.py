#!/usr/bin/env python3
"""Tests de kanban.py (unittest, bibliothèque standard seulement).

Usage : python3 -I -B scripts/selftest.py   (à relancer après toute modification de kanban.py)
"""
import contextlib
import importlib.util
import io
import re
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("kanban.py")


def charger_kanban():
    # Le script se lance avec « python3 -I » : son dossier n'est pas dans sys.path.
    spec = importlib.util.spec_from_file_location("kanban", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kanban = charger_kanban()


class DepotDeTest:
    """Un dépôt git jetable avec un backlog : config.yml, des tickets et des documents."""

    def __init__(self, config="projet: Boutique\nprefixe: BOU\n"):
        self._dossier = tempfile.TemporaryDirectory()
        self.racine = Path(self._dossier.name).resolve()
        (self.racine / ".git").mkdir()
        self.backlog = self.racine / "docs" / "backlog"
        (self.backlog / "tickets").mkdir(parents=True)
        self.ecrire("docs/backlog/config.yml", config)

    def ecrire(self, relatif, texte):
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")
        return chemin

    def avec_ticket(self, cle, titre, **champs):
        tous = {"cle": cle, "titre": titre, "type": "story", "statut": "a-cadrer", "cree": "2026-10-22", **champs}
        self.ecrire(f"docs/backlog/tickets/{cle}-{kanban.slug(titre)}.md",
                    kanban.contenu_ticket(tous, "Le besoin."))
        return self

    def avec_document(self, relatif, texte):
        self.ecrire(relatif, texte)
        return self

    def fermer(self):
        self._dossier.cleanup()


def port_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServeurEnDirect(unittest.TestCase):
    """« kanban.py serve » lancé pour de vrai, interrogé sur 127.0.0.1."""

    def setUp(self):
        self.depot = (DepotDeTest()
                      .avec_ticket("BOU-1", "Première ouverture", fiche="docs/specs/onboarding.md")
                      .avec_document("docs/specs/onboarding.md", FICHE_ONBOARDING)
                      .avec_document("docs/documentation/INDEX.md", "# Boutique\n\n[Glossaire](glossaire.md)\n")
                      .avec_document("docs/documentation/glossaire.md", "# Glossaire\n\n### Niveau\n- CP à CM2\n"))
        self.addCleanup(self.depot.fermer)
        self.port = port_libre()
        self.serveur = subprocess.Popen(
            [sys.executable, "-I", "-B", str(SCRIPT), "--dossier", str(self.depot.backlog),
             "serve", "--pas-ouvrir", "--port", str(self.port)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.arreter)
        self.annonce = self.serveur.stdout.readline()  # « Tableau en direct sur … » : le serveur écoute

    def arreter(self):
        self.serveur.terminate()
        self.serveur.wait(timeout=5)
        self.serveur.stdout.close()
        self.serveur.stderr.close()

    def lire(self, chemin):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{chemin}", timeout=5) as r:
                return r.status, r.headers.get("Content-Type"), r.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            exc.close()
            return exc.code, None, None

    def test_sert_le_tableau_a_la_racine(self):
        code, type_, corps = self.lire("/")

        self.assertEqual((code, type_), (200, "text/html; charset=utf-8"))
        self.assertIn("<title>Boutique · backlog</title>", corps)

    def test_sert_l_empreinte_du_backlog_pour_le_rechargement_en_direct(self):
        code, type_, corps = self.lire("/etat")

        self.assertEqual((code, type_), (200, "text/plain; charset=utf-8"))
        self.assertRegex(corps, r"^[0-9a-f]{16}$")

    def test_ne_sert_rien_d_autre(self):
        code, _, _ = self.lire("/config.yml")

        self.assertEqual(code, 404)

    def test_annonce_l_adresse_du_tableau_et_celle_de_la_documentation(self):
        self.assertIn(f"http://127.0.0.1:{self.port}/ ", self.annonce)
        self.assertIn(f"http://127.0.0.1:{self.port}/doc/ ", self.annonce)

    def test_sert_la_page_d_index_de_la_documentation(self):
        code, type_, corps = self.lire("/doc/")

        self.assertEqual((code, type_), (200, "text/html; charset=utf-8"))
        self.assertIn('<a href="/doc/docs/specs/onboarding.md">Onboarding</a>', corps)
        self.assertIn('<a href="/doc/docs/documentation/INDEX.md">Boutique</a>', corps)

    def test_sert_une_fiche_avec_ses_scenarios(self):
        code, type_, corps = self.lire("/doc/docs/specs/onboarding.md")

        self.assertEqual((code, type_), (200, "text/html; charset=utf-8"))
        self.assertIn("<h1>Onboarding</h1>", corps)
        self.assertIn('<span class="gk-mot">Scénario:</span>', corps)

    def test_ne_sert_pas_un_fichier_hors_des_dossiers_de_documentation(self):
        code, _, _ = self.lire("/doc/docs/backlog/config.yml")

        self.assertEqual(code, 404)


class AmorcageDuBacklog(unittest.TestCase):

    def test_config_yml_signale_les_dossiers_de_documentation_par_defaut(self):
        with tempfile.TemporaryDirectory() as dossier, contextlib.redirect_stdout(io.StringIO()):
            kanban.main(["--dossier", dossier, "init", "--projet", "Boutique", "--prefixe", "BOU"])
            config = (Path(dossier) / "config.yml").read_text(encoding="utf-8")

        self.assertIn("\n# documentation: [docs/specs, docs/documentation]", config)


class PanneauDuTableau(unittest.TestCase):
    """Le panneau d'un ticket affiche le ticket et sa fiche, rendus par le même rendu que la documentation."""

    def test_recoit_le_ticket_sans_son_titre_et_sa_fiche_deja_rendus(self):
        depot = (DepotDeTest()
                 .avec_ticket("BOU-1", "Première ouverture", fiche="docs/specs/onboarding.md")
                 .avec_document("docs/specs/onboarding.md", "# Onboarding\n"))
        self.addCleanup(depot.fermer)

        ticket, = kanban.donnees_html(kanban.Backlog(depot.backlog), live=False)["tickets"]

        self.assertEqual(ticket["corpsHtml"], "<h2>Résumé</h2>\n<p>Le besoin.</p>\n<h2>Notes de cadrage</h2>\n"
                                              "<h2>Suivi</h2>\n<ul>\n<li>2026-10-22 · créé</li>\n</ul>")
        self.assertEqual(ticket["ficheHtml"], "<h1>Onboarding</h1>")


class TableauVersLaDocumentation(unittest.TestCase):
    """Les données du tableau en direct mènent à la documentation ; le fichier HTML autonome, sans serveur, non."""

    def setUp(self):
        self.depot = (DepotDeTest()
                      .avec_ticket("BOU-1", "Première ouverture", fiche="docs/specs/onboarding.md")
                      .avec_document("docs/specs/onboarding.md", "# Onboarding\n"))
        self.addCleanup(self.depot.fermer)

    def donnees(self, live):
        return kanban.donnees_html(kanban.Backlog(self.depot.backlog), live)

    def test_le_tableau_en_direct_mene_a_la_documentation(self):
        self.assertEqual(self.donnees(live=True)["documentation"], "/doc/")
        self.assertIsNone(self.donnees(live=False)["documentation"])

    def test_le_champ_fiche_d_un_ticket_mene_a_la_page_de_sa_fiche(self):
        ticket, = self.donnees(live=True)["tickets"]

        self.assertEqual(ticket["ficheUrl"], "/doc/docs/specs/onboarding.md")

    def test_pas_de_page_pour_une_fiche_hors_de_la_documentation_ou_sans_serveur(self):
        self.depot.avec_ticket("BOU-2", "Temps partiel", fiche="notes/temps-partiel.md")
        self.depot.avec_document("notes/temps-partiel.md", "# Temps partiel\n")

        en_direct = {t["cle"]: t["ficheUrl"] for t in self.donnees(live=True)["tickets"]}
        autonome = {t["cle"]: t["ficheUrl"] for t in self.donnees(live=False)["tickets"]}

        self.assertIsNone(en_direct["BOU-2"])
        self.assertEqual(autonome, {"BOU-1": None, "BOU-2": None})


class RoutesDeLaDocumentation(unittest.TestCase):
    """Ce que « serve » répond à chaque adresse, sans passer par le réseau."""

    def setUp(self):
        self.depot = (DepotDeTest()
                      .avec_document("docs/specs/onboarding.md", "# Onboarding\n")
                      .avec_document("docs/backlog/README.md", "# Backlog\n"))
        self.addCleanup(self.depot.fermer)

    def reponse(self, cible):
        return kanban.reponse(self.depot.backlog, cible)

    def test_l_index_de_la_documentation_avec_ou_sans_barre_finale(self):
        for cible in ("/doc", "/doc/?vue=1"):
            code, type_, corps = self.reponse(cible)
            self.assertEqual((code, type_), (200, kanban.HTML), cible)
            self.assertIn("<h1>Documentation de Boutique</h1>", corps, cible)

    def test_une_page_a_l_adresse_de_son_chemin_depuis_la_racine_du_depot(self):
        self.depot.avec_document("docs/specs/journée type.md", "# Journée type\n")

        code, type_, corps = self.reponse("/doc/docs/specs/journ%C3%A9e%20type.md")

        self.assertEqual((code, type_), (200, kanban.HTML))
        self.assertIn("<h1>Journée type</h1>", corps)

    def test_l_empreinte_de_la_documentation_pour_le_rechargement_en_direct(self):
        code, type_, corps = self.reponse("/etat/documentation")

        self.assertEqual((code, type_), (200, kanban.TEXTE))
        self.assertEqual(corps, kanban.Backlog(self.depot.backlog).documentation().etat())

    def test_chaque_page_surveille_l_empreinte_de_la_documentation(self):
        etat = kanban.Backlog(self.depot.backlog).documentation().etat()
        for cible in ("/doc/", "/doc/docs/specs/onboarding.md"):
            corps = self.reponse(cible)[2]
            self.assertIn(f'const etat = "{etat}";', corps, cible)
            self.assertIn('fetch("/etat/documentation"', corps, cible)

    def test_introuvable_hors_des_dossiers_de_documentation(self):
        for cible in ("/doc/docs/backlog/README.md", "/doc/docs/specs/%2E%2E/backlog/README.md",
                      f"/doc/{self.depot.racine}/docs/specs/onboarding.md", "/doc/docs/specs/absente.md"):
            self.assertEqual(self.reponse(cible)[0], 404, cible)


class DossiersDeDocumentation(unittest.TestCase):
    """La clé « documentation » de config.yml : les dossiers servis, relatifs à la racine du dépôt."""

    def test_sans_cle_les_fiches_et_la_documentation_du_projet(self):
        self.assertEqual(kanban.dossiers_documentation({"projet": "Boutique"}),
                         ["docs/specs", "docs/documentation"])

    def test_une_liste_de_dossiers(self):
        self.assertEqual(kanban.dossiers_documentation({"documentation": ["docs/specs", "docs/adr"]}),
                         ["docs/specs", "docs/adr"])

    def test_un_seul_dossier_ecrit_sans_crochets(self):
        self.assertEqual(kanban.dossiers_documentation({"documentation": "docs/specs"}), ["docs/specs"])


class ResolutionDesDocuments(unittest.TestCase):
    """Seuls les fichiers .md des dossiers de documentation, sous la racine du dépôt, sont servis."""

    def setUp(self):
        self.depot = DepotDeTest().avec_document("docs/specs/onboarding.md", "# Onboarding\n")
        self.addCleanup(self.depot.fermer)
        self.documentation = kanban.Documentation(self.depot.racine, ["docs/specs"])

    def test_un_fichier_markdown_d_un_dossier_de_documentation(self):
        self.assertEqual(self.documentation.document("docs/specs/onboarding.md"),
                         self.depot.racine / "docs/specs/onboarding.md")

    def test_refuse_un_fichier_qui_n_est_pas_du_markdown(self):
        self.depot.ecrire("docs/specs/maquette.html", "<p>maquette</p>")

        self.assertIsNone(self.documentation.document("docs/specs/maquette.html"))

    def test_refuse_un_fichier_markdown_hors_des_dossiers_de_documentation(self):
        self.depot.ecrire("docs/backlog/README.md", "# Backlog\n")

        self.assertIsNone(self.documentation.document("docs/backlog/README.md"))

    def test_refuse_de_remonter_hors_d_un_dossier_de_documentation(self):
        self.depot.ecrire("docs/backlog/README.md", "# Backlog\n")

        self.assertIsNone(self.documentation.document("docs/specs/../backlog/README.md"))

    def test_refuse_un_lien_symbolique_qui_sort_du_depot(self):
        ailleurs = tempfile.TemporaryDirectory()
        self.addCleanup(ailleurs.cleanup)
        secret = Path(ailleurs.name) / "secret.md"
        secret.write_text("# Secret\n", encoding="utf-8")
        (self.depot.racine / "docs/specs/secret.md").symlink_to(secret)

        self.assertIsNone(self.documentation.document("docs/specs/secret.md"))

    def test_refuse_un_dossier_de_documentation_qui_est_un_lien_hors_du_depot(self):
        ailleurs = tempfile.TemporaryDirectory()
        self.addCleanup(ailleurs.cleanup)
        (Path(ailleurs.name) / "secret.md").write_text("# Secret\n", encoding="utf-8")
        (self.depot.racine / "docs/adr").symlink_to(ailleurs.name, target_is_directory=True)
        documentation = kanban.Documentation(self.depot.racine, ["docs/adr"])

        self.assertIsNone(documentation.document("docs/adr/secret.md"))

    def test_refuse_un_lien_markdown_vers_un_fichier_qui_n_en_est_pas(self):
        self.depot.ecrire("docs/specs/notes.txt", "notes")
        (self.depot.racine / "docs/specs/notes.md").symlink_to("notes.txt")

        self.assertIsNone(self.documentation.document("docs/specs/notes.md"))

    def test_rien_pour_un_document_absent(self):
        self.assertIsNone(self.documentation.document("docs/specs/absente.md"))


class SommaireDeLaDocumentation(unittest.TestCase):
    """Les rubriques de la page d'index : un dossier de documentation chacune, avec ses pages."""

    def setUp(self):
        self.depot = DepotDeTest()
        self.addCleanup(self.depot.fermer)

    def rubriques(self, *dossiers):
        return kanban.Documentation(self.depot.racine, list(dossiers)).sommaire()

    def test_les_pages_d_un_dossier_avec_leur_titre_dans_l_ordre_des_chemins(self):
        self.depot.avec_document("docs/specs/temps-partiel.md", "# Temps partiel\n")
        self.depot.avec_document("docs/specs/onboarding.md", "Statut : prête\n\n# Onboarding\n")

        rubrique, = self.rubriques("docs/specs")

        self.assertEqual(rubrique.dossier, "docs/specs")
        self.assertEqual(rubrique.pages, [kanban.Page("docs/specs/onboarding.md", "Onboarding"),
                                          kanban.Page("docs/specs/temps-partiel.md", "Temps partiel")])

    def test_une_page_sans_titre_prend_le_nom_de_son_fichier(self):
        self.depot.avec_document("docs/specs/brouillon.md", "## Pourquoi\n")

        rubrique, = self.rubriques("docs/specs")

        self.assertEqual(rubrique.pages, [kanban.Page("docs/specs/brouillon.md", "brouillon.md")])

    def test_le_point_d_entree_d_un_dossier_passe_en_tete(self):
        self.depot.avec_document("docs/documentation/Annexe.md", "# Annexe\n")
        self.depot.avec_document("docs/documentation/index.md", "# Boutique\n")

        rubrique, = self.rubriques("docs/documentation")

        self.assertEqual([p.chemin for p in rubrique.pages],
                         ["docs/documentation/index.md", "docs/documentation/Annexe.md"])
        self.assertTrue(rubrique.pages[0].est_point_d_entree)
        self.assertFalse(rubrique.pages[1].est_point_d_entree)

    def test_un_dossier_absent_donne_une_rubrique_vide_qui_le_dit(self):
        self.depot.avec_document("docs/specs/onboarding.md", "# Onboarding\n")

        specs, documentation = self.rubriques("docs/specs", "docs/documentation")

        self.assertTrue(specs.existe)
        self.assertEqual((documentation.existe, documentation.pages), (False, []))

    def test_ne_liste_pas_ce_qui_ne_serait_pas_servi(self):
        ailleurs = tempfile.TemporaryDirectory()
        self.addCleanup(ailleurs.cleanup)
        secret = Path(ailleurs.name) / "secret.md"
        secret.write_text("# Titre secret\n", encoding="utf-8")
        self.depot.avec_document("docs/specs/onboarding.md", "# Onboarding\n")
        (self.depot.racine / "docs/specs/secret.md").symlink_to(secret)

        rubrique, = self.rubriques("docs/specs")

        self.assertEqual(rubrique.pages, [kanban.Page("docs/specs/onboarding.md", "Onboarding")])

    def test_les_pages_des_sous_dossiers_suivent_celles_du_dossier(self):
        for chemin in ("regles/calendrier.md", "regles/INDEX.md", "glossaire.md", "INDEX.md"):
            self.depot.avec_document(f"docs/documentation/{chemin}", "# Page\n")

        rubrique, = self.rubriques("docs/documentation")

        self.assertEqual([p.chemin for p in rubrique.pages],
                         ["docs/documentation/INDEX.md", "docs/documentation/glossaire.md",
                          "docs/documentation/regles/INDEX.md", "docs/documentation/regles/calendrier.md"])

    def test_un_dossier_configure_hors_du_depot_ne_donne_aucune_page(self):
        ailleurs = tempfile.TemporaryDirectory()
        self.addCleanup(ailleurs.cleanup)
        (Path(ailleurs.name) / "secret.md").write_text("# Secret\n", encoding="utf-8")

        absolu, remontant = self.rubriques(ailleurs.name, f"../{Path(ailleurs.name).name}")

        self.assertEqual((absolu.pages, remontant.pages), ([], []))


class EmpreinteDeLaDocumentation(unittest.TestCase):
    """L'empreinte que les pages de documentation surveillent pour se recharger en direct."""

    def setUp(self):
        self.depot = DepotDeTest().avec_document("docs/specs/onboarding.md", "# Onboarding\n")
        self.addCleanup(self.depot.fermer)
        self.documentation = kanban.Documentation(self.depot.racine, ["docs/specs"])

    def test_change_quand_une_page_change(self):
        avant = self.documentation.etat()

        self.depot.avec_document("docs/specs/onboarding.md", "# Onboarding\n\nUne règle de plus.\n")

        self.assertNotEqual(self.documentation.etat(), avant)

    def test_change_quand_une_page_apparait(self):
        avant = self.documentation.etat()

        self.depot.avec_document("docs/specs/temps-partiel.md", "# Temps partiel\n")

        self.assertNotEqual(self.documentation.etat(), avant)

    def test_ne_change_pas_tant_que_rien_ne_change(self):
        self.assertEqual(self.documentation.etat(), self.documentation.etat())


def corps_de_page(page):
    """Le contenu d'une page de documentation, sans son en-tête ni son style : des échecs lisibles."""
    return page.split('<div class="page">', 1)[1].split("</div>\n<script>", 1)[0]


class PageDuSommaire(unittest.TestCase):
    """La page d'index de la documentation, servie sur /doc/."""

    def setUp(self):
        self.depot = DepotDeTest()
        self.addCleanup(self.depot.fermer)

    def page(self):
        return corps_de_page(kanban.page_sommaire(kanban.Backlog(self.depot.backlog)))

    def test_ramene_au_tableau(self):
        self.assertIn('<nav class="fil"><a href="/">Tableau</a> › Documentation</nav>\n'
                      "<h1>Documentation de Boutique</h1>", self.page())

    def test_un_lien_vers_chaque_page_avec_son_titre(self):
        self.depot.avec_document("docs/specs/onboarding.md", "# Onboarding\n")

        self.assertIn('<a href="/doc/docs/specs/onboarding.md">Onboarding</a>', self.page())

    def test_dit_qu_un_dossier_de_documentation_n_existe_pas_encore(self):
        self.assertIn("Aucune page pour l’instant : le dossier docs/documentation n’existe pas.", self.page())

    def test_dit_qu_un_dossier_de_documentation_n_a_pas_encore_de_page(self):
        (self.depot.racine / "docs/specs").mkdir()

        self.assertIn('<h2>docs/specs</h2><p class="vide">Aucune page pour l’instant.</p>', self.page())

    def test_signale_le_point_d_entree_d_un_dossier(self):
        self.depot.avec_document("docs/documentation/INDEX.md", "# Boutique\n")

        self.assertIn('<a href="/doc/docs/documentation/INDEX.md">Boutique</a>'
                      ' <span class="badge">point d’entrée</span>',
                      self.page())


class PageDUnDocument(unittest.TestCase):
    """La page d'un document, servie sur /doc/<chemin depuis la racine du dépôt>."""

    def setUp(self):
        self.depot = DepotDeTest().avec_document("docs/specs/onboarding.md", "# Onboarding\n\nLe **besoin**.\n")
        self.addCleanup(self.depot.fermer)

    def page(self, chemin="docs/specs/onboarding.md"):
        return kanban.page_document(kanban.Backlog(self.depot.backlog), chemin)

    def test_le_document_rendu_sous_un_fil_qui_ramene_a_la_documentation_et_au_tableau(self):
        self.assertEqual(corps_de_page(self.page()),
                         '\n<nav class="fil"><a href="/">Tableau</a> › <a href="/doc/">Documentation</a> › '
                         '<span class="chemin">docs/specs/onboarding.md</span></nav>\n'
                         '<article class="md">\n<h1>Onboarding</h1>\n'
                         '<p>Le <strong>besoin</strong>.</p>\n</article>\n')

    def test_l_onglet_porte_le_titre_du_document(self):
        self.assertEqual(re.search(r"<title>(.*)</title>", self.page()).group(1), "Onboarding · Boutique")

    def test_rien_pour_un_document_qui_n_est_pas_a_servir(self):
        self.assertIsNone(self.page("docs/backlog/config.yml"))

    def test_la_fiche_mene_aux_tickets_qui_la_designent(self):
        self.depot.avec_ticket("BOU-1", "Première ouverture", fiche="docs/specs/onboarding.md")
        self.depot.avec_ticket("BOU-2", "Temps partiel", fiche="docs/specs/temps-partiel.md")

        self.assertIn('<p class="sous">Fiche de <a href="/#BOU-1">BOU-1 · Première ouverture</a></p>',
                      corps_de_page(self.page()))


def html(markdown):
    return kanban.markdown_en_html(markdown)


class RenduDesParagraphes(unittest.TestCase):

    def test_un_paragraphe_au_texte_echappe(self):
        self.assertEqual(html('Un <script> & des "guillemets"'),
                         "<p>Un &lt;script&gt; &amp; des &quot;guillemets&quot;</p>")

    def test_une_ligne_vide_separe_deux_paragraphes(self):
        self.assertEqual(html("Première ligne\nsuite du paragraphe\n\nDeuxième paragraphe\n"),
                         "<p>Première ligne\nsuite du paragraphe</p>\n<p>Deuxième paragraphe</p>")

    def test_deux_espaces_ou_un_antislash_en_fin_de_ligne_forcent_le_retour_a_la_ligne(self):
        self.assertEqual(html("Question  \nRéponse\\\nMémoire : R-024  "),
                         "<p>Question<br>\nRéponse<br>\nMémoire : R-024</p>")


class RenduDesTitres(unittest.TestCase):

    def test_un_titre_par_niveau_de_dieses(self):
        self.assertEqual(html("# Glossaire\n## Niveau\n###### Détail"),
                         "<h1>Glossaire</h1>\n<h2>Niveau</h2>\n<h6>Détail</h6>")

    def test_un_titre_termine_le_paragraphe_qui_le_precede(self):
        self.assertEqual(html("Le besoin.\n## Suivi"), "<p>Le besoin.</p>\n<h2>Suivi</h2>")

    def test_un_titre_garde_sa_mise_en_forme(self):
        self.assertEqual(html("## La commande `kanban serve`"), "<h2>La commande <code>kanban serve</code></h2>")

    def test_les_dieses_de_fermeture_ne_font_pas_partie_du_titre(self):
        self.assertEqual(html("## Suivi ##"), "<h2>Suivi</h2>")


class RenduEnLigne(unittest.TestCase):

    def test_le_gras(self):
        self.assertEqual(html("**Question** posée"), "<p><strong>Question</strong> posée</p>")

    def test_l_italique_avec_une_etoile_ou_un_souligne(self):
        self.assertEqual(html("un *rythme* et une _quotité_"), "<p>un <em>rythme</em> et une <em>quotité</em></p>")

    def test_pas_d_italique_entre_les_soulignes_d_un_mot(self):
        self.assertEqual(html("les champs synchro_jira et empreinte_jira"),
                         "<p>les champs synchro_jira et empreinte_jira</p>")

    def test_le_code_en_ligne_garde_son_texte_tel_quel(self):
        self.assertEqual(html("lancer `kanban **serve** <port>` puis"),
                         "<p>lancer <code>kanban **serve** &lt;port&gt;</code> puis</p>")

    def test_les_caracteres_de_controle_du_fichier_sont_retires(self):
        self.assertEqual(html("a\x000\x00b\x1b"), "<p>a0b</p>")

    def test_un_antislash_garde_le_caractere_qui_le_suit_tel_quel(self):
        self.assertEqual(html(r"\*pas en italique\* ni \`en code\`"), "<p>*pas en italique* ni `en code`</p>")


class RenduDesListes(unittest.TestCase):

    def test_une_liste_a_puces(self):
        self.assertEqual(html("- CP\n- **CE1**\n- CE2"),
                         "<ul>\n<li>CP</li>\n<li><strong>CE1</strong></li>\n<li>CE2</li>\n</ul>")

    def test_une_liste_termine_le_paragraphe_qui_la_precede(self):
        self.assertEqual(html("Dans cette tranche :\n- le rythme"),
                         "<p>Dans cette tranche :</p>\n<ul>\n<li>le rythme</li>\n</ul>")

    def test_une_liste_dans_une_liste(self):
        self.assertEqual(html("- Dans cette tranche :\n  - le rythme\n  - la quotité\n- Plus tard : la zone"),
                         "<ul>\n<li>Dans cette tranche :\n"
                         "<ul>\n<li>le rythme</li>\n<li>la quotité</li>\n</ul></li>\n"
                         "<li>Plus tard : la zone</li>\n</ul>")

    def test_une_ligne_qui_continue_l_item_sans_retrait(self):
        self.assertEqual(html("- Statut : confirmée\nsuite de la source\n- Deuxième"),
                         "<ul>\n<li>Statut : confirmée\nsuite de la source</li>\n<li>Deuxième</li>\n</ul>")

    def test_une_liste_numerotee(self):
        self.assertEqual(html("1. Le rythme\n2. La quotité"),
                         "<ol>\n<li>Le rythme</li>\n<li>La quotité</li>\n</ol>")

    def test_une_liste_numerotee_garde_son_premier_numero(self):
        self.assertEqual(html("3. Les jours travaillés"), '<ol start="3">\n<li>Les jours travaillés</li>\n</ol>')

    def test_une_autre_sorte_de_puce_commence_une_autre_liste(self):
        self.assertEqual(html("1. Un\n- puce"), "<ol>\n<li>Un</li>\n</ol>\n<ul>\n<li>puce</li>\n</ul>")

    def test_une_ligne_vide_entre_deux_items_aere_la_liste_sans_la_couper(self):
        self.assertEqual(html("1. Un\n\n2. Deux"), "<ol>\n<li><p>Un</p></li>\n<li><p>Deux</p></li>\n</ol>")

    def test_un_item_garde_ce_qui_est_retire_apres_une_ligne_vide(self):
        self.assertEqual(html("- Un\n\n  suite de l'item\n- Deux"),
                         "<ul>\n<li><p>Un</p>\n<p>suite de l&#x27;item</p></li>\n<li><p>Deux</p></li>\n</ul>")


class RenduDesBlocsDeCode(unittest.TestCase):

    def test_un_bloc_de_code_garde_son_texte_echappe(self):
        self.assertEqual(html("```\nsi a < b && c\n  # pas un titre\n```"),
                         "<pre><code>si a &lt; b &amp;&amp; c\n  # pas un titre</code></pre>")

    def test_le_langage_du_bloc_devient_sa_classe(self):
        self.assertEqual(html("~~~sh\nkanban serve\n~~~"),
                         '<pre><code class="language-sh">kanban serve</code></pre>')

    def test_seule_une_cloture_aussi_longue_du_meme_signe_ferme_le_bloc(self):
        self.assertEqual(html("````md\n```\n~~~~\n````"), '<pre><code class="language-md">```\n~~~~</code></pre>')


class RenduDesCommentaires(unittest.TestCase):

    def test_un_commentaire_html_n_apparait_pas_sauf_dans_un_bloc_de_code(self):
        self.assertEqual(html("Avant<!-- note\nsur deux lignes --> après\n\n"
                              "<!-- Brouillon -->\n```\n<!-- gardé -->\n```"),
                         "<p>Avant après</p>\n<pre><code>&lt;!-- gardé --&gt;</code></pre>")


class RenduDesFilets(unittest.TestCase):

    def test_une_ligne_de_tirets_d_etoiles_ou_de_soulignes_separe_deux_parties(self):
        self.assertEqual(html("Avant\n\n---\n***\n- - -\n___\n\nAprès"),
                         "<p>Avant</p>\n<hr>\n<hr>\n<hr>\n<hr>\n<p>Après</p>")


class RenduDesCitations(unittest.TestCase):

    def test_une_citation_garde_ses_retours_a_la_ligne_comme_une_reponse_mot_pour_mot(self):
        self.assertEqual(html("**Réponse**\n> Oui, reco.\n> Et le **mercredi** aussi.\n\nMémoire : R-024"),
                         "<p><strong>Réponse</strong></p>\n<blockquote>\n"
                         "<p>Oui, reco.<br>\nEt le <strong>mercredi</strong> aussi.</p>\n"
                         "</blockquote>\n<p>Mémoire : R-024</p>")


class RenduDesTableaux(unittest.TestCase):

    def test_un_tableau_a_une_ligne_d_en_tete_et_des_lignes_de_donnees(self):
        self.assertEqual(html("| Fichier | À lire quand… |\n|---|---|\n"
                              "| [contexte.md](contexte.md) | **toujours** |"),
                         "<table>\n<thead>\n<tr><th>Fichier</th><th>À lire quand…</th></tr>\n</thead>\n<tbody>\n"
                         '<tr><td><a href="contexte.md">contexte.md</a></td>'
                         '<td><strong>toujours</strong></td></tr>\n'
                         "</tbody>\n</table>")

    def test_une_barre_echappee_reste_dans_sa_cellule(self):
        self.assertIn("<tr><td>matin <code>|</code> après-midi</td><td>2</td></tr>",
                      html("| Demi-journées | Nombre |\n|---|---|\n| matin `\\|` après-midi | 2 |"))


def gherkin(*lignes):
    return html("```gherkin\n" + "\n".join(lignes) + "\n```")


def rendu_gherkin(contenu):
    return f'<pre><code class="language-gherkin">{contenu}</code></pre>'


class RenduDuGherkin(unittest.TestCase):
    """Les blocs ```gherkin des fiches : mots-clés, titres, commentaires et variables mis en valeur."""

    def test_le_mot_cle_d_une_etape(self):
        self.assertEqual(gherkin("    Quand j'ouvre Boutique"),
                         rendu_gherkin('    <span class="gk-mot">Quand</span> j&#x27;ouvre Boutique'))

    def test_le_mot_cle_et_le_titre_d_un_scenario(self):
        self.assertEqual(gherkin("  Plan du scénario: Classe à un ou plusieurs niveaux"),
                         rendu_gherkin('  <span class="gk-mot">Plan du scénario:</span>'
                                       '<span class="gk-titre"> Classe à un ou plusieurs niveaux</span>'))

    def test_les_variables_d_un_plan_du_scenario(self):
        self.assertEqual(gherkin("    Alors Boutique présente ma classe en <niveaux présentés>"),
                         rendu_gherkin('    <span class="gk-mot">Alors</span> Boutique présente ma classe en '
                                       '<span class="gk-variable">&lt;niveaux présentés&gt;</span>'))

    def test_un_commentaire_reste_un_commentaire(self):
        self.assertEqual(gherkin("# language: fr", "  # Quand <rien> n'est dit"),
                         rendu_gherkin('<span class="gk-commentaire"># language: fr</span>\n'
                                       '  <span class="gk-commentaire">'
                                       '# Quand &lt;rien&gt; n&#x27;est dit</span>'))


class RenduDesLiens(unittest.TestCase):

    def test_un_lien_relatif_mene_a_l_autre_page_dans_le_meme_onglet(self):
        self.assertEqual(html("voir le [glossaire](glossaire.md)"),
                         '<p>voir le <a href="glossaire.md">glossaire</a></p>')

    def test_un_lien_vers_un_autre_site_s_ouvre_dans_un_autre_onglet(self):
        self.assertEqual(html("[Jira](https://exemple.atlassian.net/browse/BOU-1?a=1&b=2)"),
                         '<p><a href="https://exemple.atlassian.net/browse/BOU-1?a=1&amp;b=2" target="_blank"'
                         ' rel="noopener noreferrer">Jira</a></p>')

    def test_un_lien_qui_executerait_du_code_ne_garde_que_son_texte(self):
        self.assertEqual(html("[clic](JavaScript:alert`1`) [image](data:text/html;base64,PHNjcmlwdD4)"),
                         "<p>clic image</p>")

    def test_un_lien_vers_une_adresse_de_courriel(self):
        self.assertEqual(html("[écrire](mailto:po@exemple.fr)"),
                         '<p><a href="mailto:po@exemple.fr">écrire</a></p>')


FICHE_ONBOARDING = """# Onboarding

## Scénarios
```gherkin
# language: fr
Fonctionnalité: Première ouverture de Boutique

  Scénario: Toute première ouverture
    Étant donné que Boutique n'a encore jamais été ouverte
    Quand j'ouvre Boutique
    Alors Boutique me présente l'onboarding
```
"""


if __name__ == "__main__":
    unittest.main()

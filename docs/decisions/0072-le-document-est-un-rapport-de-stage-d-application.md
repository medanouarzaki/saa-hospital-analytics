# ADR 0072 — Le document est un rapport de stage d'application, et sa page de garde annonçait autre chose

**Statut.** Accepté.

---

## Contexte

La page de garde composait, en corps le plus gros de la page, **« Rapport de projet de fin
d'études »**. Le document n'en est pas un : c'est un rapport de stage d'application, encadré par le
chef du service d'accueil et d'admission.

Ce n'est pas une nuance de vocabulaire. Le genre du document commande tout l'appareil de la page de
garde — qui l'encadre, qui le juge, ce qu'il faut nommer — et il commande aussi ce que le lecteur
attend du contenu. Un rapport de stage annoncé comme un projet de fin d'études promet une
soutenance devant un jury qui n'existe pas.

## Décision

**Le titre devient « Rapport de stage d'application ».** Le sous-titre — « Chaîne de données et
tableau de bord pour un établissement hospitalier » — ne change pas : il décrit le travail, pas son
cadre académique.

**Le balayage a été fait sur le dépôt entier avant la correction**, et il n'a rendu qu'une
occurrence :

```
$ git grep -n -i "fin d.études\|fin d.etudes\|PFE\|projet de fin"
report/liminaires/page-de-garde.tex:19:{\Huge\bfseries Rapport de projet de fin d'études\par}
```

Le motif n'est pas muet : il trouve bien cette ligne-là, qui est le cas positif connu. Aucune autre
source de composition, aucun fichier de présentation du dépôt, aucun enregistrement de décision ne
porte l'erreur.

## Ce qui a été écarté

**Corriger aussi le vocabulaire de soutenance ailleurs dans le dépôt.** Écarté ici : un
rapport de stage d'application se soutient aussi, et rien n'établit que « soutenance » soit fautif.
Le marqueur de date de soutenance est conservé, et la ligne qui le porte disparaît tant qu'il est
vide — voir `0073`.

## Ce que cette décision ne peut pas voir

**Aucun contrôle ne tient ce titre.** Il est écrit une fois dans une source de composition, et rien
ne rougirait s'il redevenait faux. Un contrôle serait possible — confronter le titre composé à une
valeur déclarée — mais il porterait sur le PDF, que le dépôt ne suit pas, ou il recopierait la
chaîne à un second endroit, ce qui déplace le problème sans le résoudre. Le titre reste donc tenu
par la relecture seule, et c'est écrit ici pour que ce ne soit pas découvert.

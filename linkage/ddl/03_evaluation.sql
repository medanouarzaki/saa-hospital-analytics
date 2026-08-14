-- Écrit à la main : voir 00_schema_linkage.sql pour la justification.
--
-- Une ligne par seuil du balayage. Les grandeurs au niveau des paires
-- (vrais positifs, faux positifs, faux négatifs, précision, rappel,
-- f-mesure) cohabitent avec des grandeurs au niveau des grappes (grappes
-- prédites, grappes exactes, enregistrements sur-fusionnés) : les deux
-- échelles répondent à des questions différentes et aucune ne se déduit de
-- l'autre. Le nombre de paires de vérité terrain est porté ici comme
-- dénominateur : aucun lecteur en aval n'a besoin d'écrire ce chiffre en dur.
--
-- Les grandeurs de grappe qui dépendent d'une comparaison à la partition
-- vraie (grappes exactement retrouvées, enregistrements sur-fusionnés)
-- portent DEUX colonnes chacune, jamais une seule : la portée RESTREINTE
-- (limitée aux enregistrements présents dans au moins une paire de vérité
-- terrain, qui exclut les singletons triviaux à retrouver) et la portée
-- GLOBALE (l'ensemble de la population), nommées sans ambiguïté par un
-- suffixe. nb_grappes_predites n'a pas cette distinction : elle ne compare
-- à aucune partition vraie, donc aucune portée ne s'y applique.

drop table if exists linkage.evaluation cascade;
create table linkage.evaluation (
    seuil double precision not null,
    vrais_positifs integer not null,
    faux_positifs integer not null,
    faux_negatifs integer not null,
    precision_valeur double precision not null,
    rappel double precision not null,
    f_mesure double precision not null,
    nb_grappes_predites integer not null,
    nb_grappes_exactes_restreint integer not null,
    nb_grappes_exactes_global integer not null,
    nb_enregistrements_sur_fusionnes_restreint integer not null,
    nb_enregistrements_sur_fusionnes_global integer not null,
    nb_paires_verite_terrain integer not null,
    constraint evaluation_pkey primary key (seuil)
);

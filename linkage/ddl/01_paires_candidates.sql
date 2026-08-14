-- Écrit à la main : voir 00_schema_linkage.sql pour la justification.
--
-- Une ligne par paire candidate évaluée par le rapprochement. L'ordre
-- canonique des deux identifiants (n_ipp_1 strictement inférieur à
-- n_ipp_2) est imposé par contrainte : il interdit à la fois la paire
-- inversée et la paire d'un enregistrement avec lui-même.
--
-- Une colonne de niveau par comparaison déclarée dans le registre
-- (linkage.champs.COMPARAISONS), préfixée "niveau_" et suffixée par le nom
-- de la comparaison : douze colonnes, une par comparaison, pas une par
-- colonne comparée (la comparaison composite pièce d'identité porte un
-- seul niveau, "niveau_piece_identite", pas deux).

drop table if exists linkage.paires_candidates cascade;
create table linkage.paires_candidates (
    n_ipp_1 text not null,
    n_ipp_2 text not null,
    probabilite double precision not null,
    poids_correspondance double precision not null,
    niveau_nom integer not null,
    niveau_nom_famille_1 integer not null,
    niveau_nom_famille_2 integer not null,
    niveau_date_naissance integer not null,
    niveau_telephone_1 integer not null,
    niveau_adresse integer not null,
    niveau_email integer not null,
    niveau_nom_pere integer not null,
    niveau_nom_mere integer not null,
    niveau_quartier integer not null,
    niveau_ville integer not null,
    niveau_piece_identite integer not null,
    regle_blocage text not null,
    constraint paires_candidates_pkey primary key (n_ipp_1, n_ipp_2),
    constraint paires_candidates_ordre_canonique check (n_ipp_1 < n_ipp_2)
);

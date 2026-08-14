-- Écrit à la main : voir 00_schema_linkage.sql pour la justification.
--
-- Une ligne par enregistrement regroupé. Le seuil est répété sur chaque
-- ligne plutôt que porté séparément : un regroupement dépend entièrement
-- du seuil auquel il a été calculé, et cette colonne rend cette dépendance
-- lisible sans jointure.

drop table if exists linkage.grappes_identite cascade;
create table linkage.grappes_identite (
    n_ipp text not null,
    grappe_id text not null,
    taille_grappe integer not null,
    seuil double precision not null,
    constraint grappes_identite_pkey primary key (n_ipp)
);

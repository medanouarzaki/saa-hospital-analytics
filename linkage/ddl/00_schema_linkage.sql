-- Écrit à la main, délibérément : le dépôt sait produire mécaniquement les
-- tables de quarantaine depuis le registre des champs, mais reproduire ce
-- mécanisme ici rendrait la correspondance entre le registre et ce schéma
-- vraie par construction. Une DDL écrite indépendamment du registre donne
-- au test de correspondance quelque chose à prouver.
--
-- Ce fichier, et les trois fichiers de table qui le suivent, reconstruisent
-- intégralement le schéma linkage à chaque application : chaque table est
-- supprimée avant d'être recréée, la création du schéma seule utilise
-- "if not exists" puisqu'un schéma n'a pas de contenu à réinitialiser.

create schema if not exists linkage;

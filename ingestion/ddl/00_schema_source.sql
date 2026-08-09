-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.
--
-- Ce fichier, et les onze fichiers de table qui le suivent, reconstruisent
-- intégralement le schéma source à chaque application, ils ne le font pas
-- évoluer par différences : chaque table est supprimée avant d'être
-- recréée.
--
-- Aucune contrainte n'est posée : ni clé primaire, ni clause d'obligation
-- de valeur, ni clé étrangère, ni index. La couche source reproduit une
-- extraction et doit accepter ce qu'une extraction contient, y compris des
-- doublons et des valeurs mal formées ; l'unicité et le typage se
-- contrôlent à la couche intermédiaire, avec mise en quarantaine. Une
-- contrainte ici rejetterait précisément les défauts que la chaîne existe
-- pour traiter.

create schema if not exists source;

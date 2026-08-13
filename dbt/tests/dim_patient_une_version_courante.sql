{#
    Exactement une version courante par n_ipp : tout n_ipp dont le nombre de versions à
    est_courante diffère de 1 rend une ligne -- couvre le cas 0 (aucune courante) et le cas
    2+ (plusieurs courantes).
#}

select
    n_ipp,
    count(*) filter (where est_courante) as n_versions_courantes
from {{ ref('dim_patient') }}
group by n_ipp
having count(*) filter (where est_courante) != 1

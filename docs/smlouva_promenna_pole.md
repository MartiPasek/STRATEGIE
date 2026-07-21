# Pracovní smlouva — proměnná pole (z anotovaného skenu Šárky, 17. 6. 2026)

Zásada (Šárka): **wording NEMĚNIT**, jen z vyznačených míst udělat volbu / doplnění.
Typy: **VOLBA** = výběr z možností · **DOPLNĚNÍ** = volný text/datum/číslo · **PER-FIRMA** = dle EC/ES automaticky.

| § / místo | Co se mění | Typ | Placeholder | Pozn. |
|---|---|---|---|---|
| Hlavička | EUROSOFT‑System **NEBO** EUROSOFT‑Control | VOLBA firmy | `{{firma_nazev}}` + per-firma blok | řídí IČ/DIČ/OR/banku/GDPR/podpis |
| Strany | jméno, datum narození, bydliště | DOPLNĚNÍ (z dat) | `{{jmeno}}`, `{{narozeni}}`, `{{bydliste}}` | z karty zaměstnance |
| §1.1 | datum nástupu | DOPLNĚNÍ (datum) | `{{smlouva_od}}` | |
| §1.1 | pozice / druh práce („do práce jako…") | DOPLNĚNÍ | `{{pozice}}` | pozn. „druh práce" |
| §1.2 | doba určitá / neurčitá | VOLBA | `{{doba}}` | + datum „do" u určité |
| §1.2 | zkušební doba (počet měsíců) | VOLBA / DOPLNĚNÍ | `{{zkusebni_doba}}` | NOVÉ (dnes natvrdo 3/4 měs.) |
| §1.3 | nahrazuje smlouvu ze dne … | DOPLNĚNÍ (volitelné) | `{{nahrazuje_dne}}` | NOVÉ, volitelné |
| §2.1 | místo výkonu práce = **jen „Plzeň"** | ZMĚNA (zkrátit) | `{{misto_vykonu}}` = „Plzeň" | dnes natvrdo plná adresa |
| §2.2 | týdenní úvazek (hodin) | DOPLNĚNÍ | `{{uvazek}}` | dnes natvrdo 40 |
| §2.3 | začátek práce nejpozději v … | VOLBA / DOPLNĚNÍ (čas) | `{{cas_zacatek}}` | NOVÉ (dnes 7:00 / 9:00) |
| §2.3 | konec práce mezi … a … | VOLBA / DOPLNĚNÍ (čas) | `{{cas_konec_od}}`, `{{cas_konec_do}}` | NOVÉ (dnes 14:30–18:00) |
| §5.2 | čas hlášení nepřítomnosti | VOLBA / DOPLNĚNÍ | `{{cas_hlaseni}}` | NOVÉ |
| §5.2 | telefon nadřízený / vedoucí divize | DOPLNĚNÍ (dle pozice/divize) | `{{tel_nadrizeny}}`, `{{tel_vedouci}}` | NOVÉ (dnes natvrdo čísla) |
| §13.8 | GDPR předpis = název firmy | PER-FIRMA | `{{firma_nazev}}` | |
| Podpis | datum podpisu | DOPLNĚNÍ (auto dnes) | `{{dnes}}` | |
| Podpis | blok podpisu | PER-FIRMA | `{{podpis_zam_html}}` | System=Marti; Control=Marti+Branislav Mózer |

## ROZHODNUTO (Šárka 17. 6. 2026): DVĚ šablony
- **Pracovní smlouva — výrobní pozice** (`smlouva_vyrobni`, id 4)
- **Pracovní smlouva — kancelářské pozice** (`smlouva_kancelar`, id 5)

Obě mají **stejnou sadu proměnných polí** z tabulky výše. Liší se jen **obsahem** odstavců:
- §2.3: výrobní = operativní nástup/nakládka; kancelář = práce na dálku.
- §13.1: výrobní = pořádek + nářadí/přístroje; kancelář = jen pořádek a čistota.
- Výchozí hodnoty proměnných se mohou lišit (např. čas začátku 7:00 vs 9:00, zkušební 4 vs 3 měs.),
  ale jsou to **doplnitelné/volitelné** hodnoty, ne natvrdo.

Náhledy k revizi: `sablony_nahled/smlouva_vyrobni_param.html`, `sablony_nahled/smlouva_kancelar_param.html`.

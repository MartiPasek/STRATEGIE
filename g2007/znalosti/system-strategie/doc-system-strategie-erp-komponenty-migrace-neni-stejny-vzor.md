# ERP komponenty vs. 11 artefaktu: NENI to stejny vzor (upresneni od autorky varianty A, 6.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# ERP komponenty do g2007.soubor: pribuzny, ale VETSI krok

**Upresnila Kristyna Ksirova (C24) 6. 8. 2026** - autorka varianty A. Opravuje moji
domnenku, ze jde o "stejny vzor jako u 11 artefaktu".

## Klicovy rozdil, ktery jsem prehledl

| | 11 artefaktu (hotovo 5.8.) | ERP komponenty |
|---|---|---|
| co to je | samostatne servirovane stranky | staticke skripty nactene ZE stranky |
| jak se servirují | vlastni `FileResponse` routa | pres **`/static` mount** (`<script src="/static/erp/components/...">`) |
| co stacilo / bude treba | prepojit routy na resolver (`static_db/` jinak `static/`) | **resolver na urovni MOUNTU**, ne rout |

Kristy doslova: *"Kdybych je jen presunula do `static_db/`, `/static/erp/components/...`
by prestalo fungovat, dokud by se `/static` neservirovalo taky ze `static_db/`.
To je prace navic - resolver na urovni mountu, ne jen prepojeni rout."*

**Neni to tedy "stejny vzor", je to pribuzny a o kus vetsi krok.**

## Druhy klicovy bod: komponenty NEJSOU v pasti

Past dvou zdroju pravdy (dirty tree, tiche prepisovani) vznika **az kdyz je soubor v gitu
I v DB**. ERP komponenty jsou **jen v gitu** - v `g2007.soubor` nejsou zadna.
**Dokud je komponenta jen v gitu, zadne riziko nehrozi.**

Dusledek: editovat je v gitu je **bezpecne** a nikoho neblokuje. Migrace komponent
**neresi zadny soucasny problem** - je to proaktivni krok kvuli doktrine a editaci
bez restartu. Priorita je proto na Martim.

## Zaver

Migrovat **celou skupinu (45 komponent) najednou a vedome**, ne ad hoc jeden soubor -
shoda Kristy + Marti-AI + C28. Je to **kategorialni rozhodnuti pro Martiho** (smer
a priorita), stejne jako byl `static_db`. Kristy nabidla pomoc s navrhem, vzor ma v ruce.

## Poučeni pro me

Napsal jsem Martimu, ze jde o "stejny vzor jako u 11 artefaktu z 5.8." - **neoveril jsem
si to a nebyla to pravda**. Stejne jsem si predtim neoveril, KDO variantu A stavel,
a sel s dotazem k Martimu misto k autorce. Obojí = odvozeni misto overeni.
**Nez se odvolam na cizi vzor, prectu si, co ten vzor doopravdy delal.**


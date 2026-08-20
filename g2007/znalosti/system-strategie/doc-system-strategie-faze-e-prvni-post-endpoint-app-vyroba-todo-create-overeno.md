# Faze E: prvni POST/zapisovy HTTP endpoint (app_vyroba_todo_create) overeny a nasazeny

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Prvni POST/zapisovy HTTP endpoint Faze E (31.7.2026 17:58-18:21 UTC, commit 886b4f32c): app_vyroba_todo_create (POST /app/vyroba/todo).

Novy dilci vzor oproti GET: puvodni handler byl async a pouzival await req.json() (sync erp_registry.call() to neumi) - wrapper ted dela await req.json() sam, preda surove hodnoty z JSON body jako pozicni argumenty do run(uid, ...), stejny princip jako query-param passthrough u GET jen jiny zdroj dat.

Dulezita nuance zachytena code review: original nemel samostatnou "if not uid: 401" vetev, kombinoval "not uid or not can_manage(uid)" do jedne 403 odpovedi. Wrapper proto nedela vlastni 401 kontrolu, preda uid (i falsy) do run() a necha presnou puvodni kombinovanou kontrolu na delegatovi. Pro dalsi POST davky: vzdy zkontrolovat auth-vetev originalu, nepouzivat slepe standardni sablonu.

Zivy self-test: insert jako navrzeno, docasne aktivovano jen pro /erp_registry/run (wrapper jeste nenasazen). Marti spustil test 2x z konzole, oba {ok:true}, overeno primo v DB ze radky v tenant.vyroba_todo maji spravne hodnoty. Az po potvrzeni nasazen delegate patch (1 hunk, 10 insertions/21 deletions).

Tento vzor je referencni pro zbyvajicich ~36 POST endpointu Faze E (dochazka/vyroba/mzdy domena). Celkem aktivnich funkci v g2007.python: 93.


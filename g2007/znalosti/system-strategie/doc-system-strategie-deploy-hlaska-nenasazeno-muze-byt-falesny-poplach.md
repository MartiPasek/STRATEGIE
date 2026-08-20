# Deploy: hlaska "cloud NENASAZENO" muze byt falesny poplach - over v deployment_proposals

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## O co jde

Most po deployi obcas napise do `CLAUDE_DEPLOY_OUT.txt`:

```
# commit: <sha> · cloud: NENASAZENO:
#   reason=None error=RemoteDisconnected: Remote end closed connection without response
```

**Tahle hlaska NEZNAMENA, ze se nenasadilo.** Deploy si sam restartuje API
(`/deploy/now` = git pull + restart marker), takze server zavre spojeni bez odpovedi
prave ve chvili, kdy nasazeni **uz probehlo**. Most odpoved nedostane a ohlasi neuspech.

## Jak to overit (nehadat)

Zdroj pravdy je evidence nasazeni **`public.deployment_proposals`**:

```sql
SELECT id, status, LEFT(commit_sha,10) AS sha,
       to_char(proposed_at,'DD.MM HH24:MI:SS') AS navrzeno,
       to_char(deploy_completed_at,'DD.MM HH24:MI:SS') AS dokonceno
FROM public.deployment_proposals
WHERE commit_sha LIKE '<tvuj sha>%';
```

`status='deployed'` = git pull na cloudu probehl a restart marker byl polozen, tedy
nasazeno. **Pozor na casy:** `watcher.log` pise v **UTC**, evidence v **lokalnim case**
(v lete +2 h). Kdyz to nezohlednis, zda se, ze zaznam chybi.

## Overene pripady (19. 8. 2026, Jirka + C28)

| Pripad | Co hlasil most | Co je v evidenci |
|---|---|---|
| Kristy/C24, commit `b41f112a` | NENASAZENO (RemoteDisconnected) | **deployed**, dokonceno 19.08 11:17:17 |
| Jirka/C28, commit `33cb649d` | NENASAZENO (HTTP 502) | **deployed**, dokonceno 18.08 12:55:31 |
| Jirka/C28, 17. 8., 2x HTTP **401** | NENASAZENO | **opravdu nenasazeno** — jina trida chyby |

Rozdil je podstatny: **401 = pozadavek server odmitl** (failover Caddy na sekundar 8003
bez tokenu), takze se opravdu nic nestalo — to je skutecny tichy propad a je od 17. 8.
osetreny opakovanim pokusu. **Utrzene spojeni a 502 = pozadavek probehl**, ztratila se
jen odpoved.

## Proc most opakuje jen u 401 (stav k 19. 8. 2026)

V `scripts/claude_sql_runner.py`, funkce `_cloud_deploy`, ma opakovani jen vetev
`except urllib.error.HTTPError` pro `e.code == 401`. Pad spojeni tam nedojde:
`RemoteDisconnected` vznika az v `h.getresponse()`, ktere urllib **neobaluje** do
`URLError` (obaleny je jen `h.request`), takze skonci v `except Exception`, ktera se
vraci hned bez opakovani. Overeno ve zdrojaku Pythonu.

## Stav opravy

Oprava je **pripravena a otestovana, ale K 19. 8. 2026 NENASAZENA** — most je sdilene
jadro vsech peti instanci, takze schvaleni patri **Martimu Paskovi** (Marti-AI ho
vyslovne odmitla dat sama a predala mu to s doporucenim, konverzace 363, msg 12959).
Navrh: opakovat i pri padu spojeni a pri 502/503/504, a hlavne vyhodnotit
`already_up_to_date` pri **dalsim** pokusu jako uspech (na prvnim pokusu zustava chybou,
tam opravdu nebylo co nasazovat). Balicek s postupem:
`\192.168.30.11\Data\ZZ_Jiri\AI_work\most_oprava_deploy_2026-08-19\`.

**Dokud to neni nasazene:** kdyz vidis NENASAZENO, nedeployuj slepe znovu — nejdriv se
podivej do `deployment_proposals`.

## Sirsi pouceni

Rodina "krok se tvari jako neuspesny/uspesny, ale skutecnost je jinde" — stejne jako
neutralni navratovky u `@@G2007ADD`. **Navratovka nastroje neni dukaz; dukaz je stav
v cilovem systemu.** Plati obema smery: nejen "hlasi OK, ale neprovedlo se", ale i
"hlasi chybu, a pritom se provedlo".


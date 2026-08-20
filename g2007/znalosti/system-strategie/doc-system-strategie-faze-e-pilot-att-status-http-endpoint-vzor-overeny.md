# Faze E pilot: prvni HTTP endpoint migrovan na g2007.python, novy vzor overeny

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Migrovan GET /app/attendance/status (kod=att_status) - prvni HTTP endpoint (na rozdil od Faze A-D, ktere migrovaly pomocne funkce volane odjinud).
NOVY VZOR: FastAPI stavi routing tabulku pri startu, takze URL + metoda + auth (_uid_from_token_or_cookie) MUSI zustat tenky async wrapper primo v router.py (jadro). Jen synchronni byznys logika (run(uid) -> plain dict) jde do g2007.python. Wrapper: auth check -> erp_registry.call(kod, uid) -> JSONResponse(vysledek). Vyjimky se propaguji stejne jako pred migraci.
Overeni pred deployem: Marti porovnal skutecny vystup pres JS konzoli (legacy GET endpoint vs. novy kod pres POST /app/erp_registry/run) - shoda bajtove presna. Az po potvrzeni deploy commit a4e0e8da6, push OK. Marti potvrdil zivy provoz po deployi: "Vsechno jede korektne".
Tenhle vzor je referencni pro zbytek Faze E (130+ HTTP endpointu router.py). U dalsich GET/read-only endpointu stejneho tvaru netreba opakovat rucni self-test pro kazdy kus; pred prvnim POST/zapisovym endpointem v Fazi E doporuceno srovnani zopakovat.


"""
RB Premium API — referenční skeleton adaptéru (Claude id=23, 24.6.2026)
=======================================================================
NENÍ zapojené do produkce. Reference podle živé Swagger spec
(https://developers.rb.cz/premium/, v1.1.20240910). Čeká na:
  - ClientID (registrace appky na portálu) -> X-IBM-Client-Id
  - mTLS certifikát .p12 + heslo (z trezoru, ephemeral)
Univerzální rozhraní providera; RB = první implementace. Normalizovaný výstup
krmí tenant.bank_transaction_raw (staging) -> párování -> ucetni_denik.
"""
from __future__ import annotations

import logging
import uuid
import time
import datetime as dt
from typing import Iterator

import requests  # přesunuto na top level — vždy dostupné, umožňuje type hint

BASE = "https://api.rb.cz/rbcz/premium/api"   # bank_provider.base_url

logger = logging.getLogger(__name__)

_MAX_TX_RANGE_DAYS = 90  # RB API limit — max zpětné okno pro transakce


class RBPremiumAdapter:
    """
    Klient pro RB Premium API (mTLS + IBM API key).

    Parametry:
        client_id      — X-IBM-Client-Id (z portálu developers.rb.cz)
        p12_pem_cert   — PEM certifikát (dešifrovaný z .p12 v paměti)
        p12_pem_key    — PEM privátní klíč (dešifrovaný z .p12 v paměti)
        psu_ip         — IP adresa koncového uživatele (PSD2 header), volitelně
        session        — vlastní requests.Session (pro testy/DI), jinak se vytvoří nová
    """

    def __init__(self, client_id: str, p12_pem_cert: str, p12_pem_key: str,
                 psu_ip: str | None = None, session: requests.Session | None = None):
        # p12 dešifruj ephemeral z trezoru -> PEM (cert, key) v paměti; NIKDY na disk/log.
        self.client_id = client_id
        self.psu_ip = psu_ip
        self.s = session or requests.Session()
        self._cert = (p12_pem_cert, p12_pem_key)   # mTLS

    # ---- nízkoúrovňové ----

    def _headers(self) -> dict:
        """Sestaví společné HTTP hlavičky pro každý požadavek."""
        h = {
            "X-IBM-Client-Id": self.client_id,
            "X-Request-Id": uuid.uuid4().hex[:60],
            "Accept": "application/json",
        }
        if self.psu_ip:
            h["PSU-IP-Address"] = self.psu_ip
        return h

    def _get(self, path: str, params: dict | None = None,
             cert: bool = True) -> requests.Response:
        """
        GET požadavek s automatickým retry při 429 (exponenciální backoff).

        Raises:
            CertInvalid: 401 — certifikát chybí nebo je zablokovaný.
            RateLimited: 429 přetrvává i po 5 pokusech.
            requests.HTTPError: jiná HTTP chyba (raise_for_status).
        """
        for attempt in range(5):
            r = self.s.get(
                BASE + path,
                headers=self._headers(),
                params=params,
                cert=self._cert if cert else None,
                timeout=30,
            )
            if r.status_code == 429:
                wait = 2 ** attempt
                logger.warning(
                    "RB API 429 rate-limit, pokus %d/5, čekám %ds", attempt + 1, wait
                )
                time.sleep(wait)
                continue
            if r.status_code == 401:
                raise CertInvalid("401 — cert chybí/zablokovaný (roční blok? odblok v IB)")
            r.raise_for_status()
            return r
        raise RateLimited("429 i po 5 retry pokusech")

    # ---- READ (Fáze 1) ----

    def list_accounts(self) -> list[dict]:
        """
        Vrátí seznam všech účtů dostupných přes API (stránkovaně).

        Returns:
            Seznam účtů — každý dict odpovídá struktuře z RB API /accounts.
        """
        out, page = [], 1
        while True:
            r = self._get("/accounts", {"page": page, "size": 50})
            if r.status_code == 204:
                break
            j = r.json()
            out += j.get("accounts", [])
            if j.get("last", True):
                break
            page += 1
        return out

    def get_balances(self, account_number: str) -> dict:
        """
        Vrátí aktuální zůstatky pro zadaný účet.

        Args:
            account_number: číslo účtu (formát dle RB API, např. CZ1234...)
        """
        return self._get(f"/accounts/{account_number}/balance").json()

    def get_transactions(self, account_number: str, ccy: str,
                         date_from: dt.date, date_to: dt.date) -> Iterator[dict]:
        """
        Iterátor přes normalizované transakce účtu v zadaném období.

        RB API omezuje rozsah na max 90 dní zpět. Validace proběhne lokálně
        ještě před voláním API — ušetří zbytečný HTTP round-trip.

        Args:
            account_number: číslo účtu
            ccy:            měna (např. "CZK")
            date_from:      počáteční datum (včetně)
            date_to:        koncové datum (včetně)

        Raises:
            ValueError: rozsah dat přesahuje 90 dní nebo date_from > date_to.
        """
        if date_from > date_to:
            raise ValueError(
                f"date_from ({date_from}) musí být ≤ date_to ({date_to})"
            )
        delta = (date_to - date_from).days
        if delta > _MAX_TX_RANGE_DAYS:
            raise ValueError(
                f"RB API: rozsah {delta} dní přesahuje maximum {_MAX_TX_RANGE_DAYS} dní. "
                "Rozděl dotaz na více volání."
            )

        page = 1
        while True:
            r = self._get(
                f"/accounts/{account_number}/{ccy}/transactions",
                {"from": date_from.isoformat(), "to": date_to.isoformat(), "page": page},
            )
            if r.status_code == 204:
                return
            j = r.json()
            for t in j.get("transactions", []):
                yield normalize_tx(t, ccy)
            if j.get("lastPage", True):
                return
            page += 1

    # ---- PLATBY (Fáze 2) — import = návrh do IB, podpis dělá ČLOVĚK v IB ----

    def import_payment_batch(self, batch_content: str, fmt: str = "SEPA-XML",
                             name: str | None = None) -> int:
        """
        Nahraje dávku plateb do IB k podpisu (podpis dělá člověk v Internet Bankingu).

        Args:
            batch_content: obsah souboru (SEPA XML nebo jiný formát dle fmt)
            fmt:           formát dávky, default "SEPA-XML"
            name:          volitelný název dávky (max 50 znaků)

        Returns:
            batchFileId — ID pro sledování stavu přes get_batch_status().
        """
        h = self._headers()
        h["Batch-Import-Format"] = fmt
        if name:
            h["Batch-Name"] = name[:50]
        r = self.s.post(
            BASE + "/payments/batches",
            headers=h,
            data=batch_content.encode("utf-8"),
            cert=self._cert,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["batchFileId"]   # -> stav přes get_batch_status; podpis v IB

    def get_batch_status(self, batch_file_id: int) -> dict:
        """
        Vrátí aktuální stav platební dávky.

        Args:
            batch_file_id: ID vrácené z import_payment_batch()
        """
        return self._get(f"/payments/batches/{batch_file_id}").json()


def normalize_tx(t: dict, ccy: str) -> dict:
    """RB transakce -> řádek pro tenant.bank_transaction_raw (univerzální tvar)."""
    amt = t.get("amount", {})
    det = (t.get("entryDetails", {}).get("transactionDetails", {}) or {})
    rp = (det.get("relatedParties", {}) or {})
    cp = (rp.get("counterParty", {}) or {})
    acc = (cp.get("account", {}) or {})
    rem = (det.get("remittanceInformation", {}) or {})
    cref = (rem.get("creditorReferenceInformation", {}) or {})
    return {
        "ext_id":    str(t.get("entryReference") or ""),
        "datum":     (t.get("bookingDate") or "")[:10] or None,
        "castka":    amt.get("value"),
        "mena":      amt.get("currency") or ccy,
        "smer":      "out" if t.get("creditDebitIndication") == "DBIT" else "in",
        "protiucet": acc.get("iban") or acc.get("accountNumber"),
        "vs":        cref.get("variable"),
        "ks":        cref.get("constant"),
        "ss":        cref.get("specific"),
        "zprava":    rem.get("unstructured") or det.get("originatorMessage"),
        "raw":       t,
    }


class CertInvalid(Exception):
    """Certifikát chybí, vypršel nebo je zablokovaný (typicky 401 od RB API)."""


class RateLimited(Exception):
    """RB API vrací 429 i po vyčerpání všech retry pokusů."""

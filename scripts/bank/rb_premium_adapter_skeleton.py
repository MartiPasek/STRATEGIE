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
import uuid, time, datetime as dt
from typing import Iterator

BASE = "https://api.rb.cz/rbcz/premium/api"   # bank_provider.base_url


class RBPremiumAdapter:
    def __init__(self, client_id: str, p12_pem_cert: str, p12_pem_key: str,
                 psu_ip: str | None = None, session=None):
        # p12 dešifruj ephemeral z trezoru -> PEM (cert,key) v paměti; NIKDY na disk/log.
        import requests  # noqa
        self.client_id = client_id
        self.psu_ip = psu_ip
        self.s = session or requests.Session()
        self._cert = (p12_pem_cert, p12_pem_key)   # mTLS

    # ---- nízkoúrovňové ----
    def _headers(self) -> dict:
        h = {"X-IBM-Client-Id": self.client_id,
             "X-Request-Id": uuid.uuid4().hex[:60]}
        if self.psu_ip:
            h["PSU-IP-Address"] = self.psu_ip
        return h

    def _get(self, path: str, params: dict | None = None, cert: bool = True):
        for attempt in range(5):
            r = self.s.get(BASE + path, headers=self._headers(), params=params,
                           cert=self._cert if cert else None, timeout=30)
            if r.status_code == 429:                       # rate limit -> backoff
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 401:
                raise CertInvalid("401 — cert chybí/zablokovaný (roční blok? odblok v IB)")
            r.raise_for_status()
            return r
        raise RateLimited("429 i po retry")

    # ---- READ (Fáze 1) ----
    def list_accounts(self) -> list[dict]:
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
        return self._get(f"/accounts/{account_number}/balance").json()

    def get_transactions(self, account_number: str, ccy: str,
                         date_from: dt.date, date_to: dt.date) -> Iterator[dict]:
        # max 90 dní zpět; stránkováno přes lastPage
        page = 1
        while True:
            r = self._get(f"/accounts/{account_number}/{ccy}/transactions",
                          {"from": date_from.isoformat(), "to": date_to.isoformat(), "page": page})
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
        import requests  # noqa
        h = self._headers(); h["Batch-Import-Format"] = fmt
        if name:
            h["Batch-Name"] = name[:50]
        r = self.s.post(BASE + "/payments/batches", headers=h,
                        data=batch_content.encode("utf-8"),
                        cert=self._cert, timeout=60)
        r.raise_for_status()
        return r.json()["batchFileId"]   # -> stav přes get_batch_status; podpis v IB

    def get_batch_status(self, batch_file_id: int) -> dict:
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
        "ext_id":   str(t.get("entryReference") or ""),
        "datum":    (t.get("bookingDate") or "")[:10] or None,
        "castka":   amt.get("value"),
        "mena":     amt.get("currency") or ccy,
        "smer":     "out" if t.get("creditDebitIndication") == "DBIT" else "in",
        "protiucet": acc.get("iban") or acc.get("accountNumber"),
        "vs":       cref.get("variable"),
        "ks":       cref.get("constant"),
        "ss":       cref.get("specific"),
        "zprava":   rem.get("unstructured") or det.get("originatorMessage"),
        "raw":      t,
    }


class CertInvalid(Exception): ...
class RateLimited(Exception): ...

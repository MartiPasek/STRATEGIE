#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Play Developer API (androidpublisher v3) — plne autonomni upload (bez file pickeru).
Servisni ucet klic: APP/Mobile/play-api-key.json (gitignored, TAJNY).

Pouziti:
  python scripts/play_api_upload.py screenshots     # nahraje snimky (phone+tablet)
  python scripts/play_api_upload.py aab             # BLOKOVANO (vypise, co si overit)
  python scripts/play_api_upload.py aab --confirm    # nahraje AAB do produkce + odesle ke kontrole

POZOR: kazdy edits.commit = NOVE odeslani ke kontrole. Zrusi pravave bezici
submission a resetuje review timer. Proto commit dela az posledni krok, kdyz je
vse ostatni (listing, Sign in details, serverove zmeny) hotove a overene.

Pojistka AAB: vyzaduje explicitni flag --confirm (jinak neudela nic).
Historie: driv se flag jmenoval --v73-approved (cekalo se na schvaleni v73).
Google v73 dne 15.7.2026 ZAMITL ("Login credentials are missing" - recenzent
se nedostal pres prihlaseni), takze zadna revize nebezi a posila se rovnou v74.
"""
import os, sys, glob
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY  = os.path.join(ROOT, "APP", "Mobile", "play-api-key.json")
PKG  = "cz.strategie.mobile"
LANG = "cs-CZ"
GFX  = os.path.join(ROOT, "docs", "google_play_grafika")
AAB  = os.path.join(ROOT, "APP", "Mobile", "app", "build", "outputs", "bundle", "playRelease", "app-play-release.aab")
SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]

def _svc():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    return build("androidpublisher", "v3", credentials=creds, cache_discovery=False)

def upload_screenshots():
    uploads = {
        "phoneScreenshots":     sorted(glob.glob(os.path.join(GFX, "play_phone_*.png"))),
        "sevenInchScreenshots": sorted(glob.glob(os.path.join(GFX, "play_tablet_*.png"))),
        "tenInchScreenshots":   sorted(glob.glob(os.path.join(GFX, "play_tablet_*.png"))),
    }
    edits = _svc().edits()
    edit_id = edits.insert(packageName=PKG, body={}).execute()["id"]
    print("editId =", edit_id)
    for itype, files in uploads.items():
        if not files:
            print("  (preskoceno)", itype); continue
        edits.images().deleteall(packageName=PKG, editId=edit_id, language=LANG, imageType=itype).execute()
        print(f"  {itype}: nahravam {len(files)}")
        for f in files:
            edits.images().upload(packageName=PKG, editId=edit_id, language=LANG, imageType=itype,
                                  media_body=MediaFileUpload(f, mimetype="image/png")).execute()
            print("     +", os.path.basename(f))
    edits.commit(packageName=PKG, editId=edit_id).execute()  # ucet posila ke kontrole automaticky
    print("COMMIT OK — snimky nahrany + odeslany ke kontrole.")

def upload_aab(confirmed):
    if not confirmed:
        print("BLOKOVANO: upload AAB = nove odeslani ke kontrole (resetuje review timer).")
        print("Nez to spustis, over, ze je hotove VSE ostatni:")
        print("  - Sign in details v Play Console (instrukce k demu pro recenzenty)")
        print("  - serverove zmeny nasazene a overene zive")
        print("Pak spust:")
        print("   python scripts/play_api_upload.py aab --confirm")
        return
    if not os.path.exists(AAB):
        print("CHYBA: AAB nenalezen:", AAB, "\n(nejdriv build: scripts/build_aab.ps1)"); return
    edits = _svc().edits()
    edit_id = edits.insert(packageName=PKG, body={}).execute()["id"]
    print("editId =", edit_id)
    bundle = edits.bundles().upload(packageName=PKG, editId=edit_id,
                                    media_body=MediaFileUpload(AAB, mimetype="application/octet-stream")).execute()
    vc = bundle["versionCode"]
    print("  nahran AAB versionCode =", vc)
    edits.tracks().update(packageName=PKG, editId=edit_id, track="production", body={
        "releases": [{
            "versionCodes": [str(vc)],
            "status": "completed",
            "releaseNotes": [{"language": LANG,
                              "text": "- Nova ikona a sjednoceny vzhled.\n- Vylepsena stabilita a podpora tabletu."}],
        }]
    }).execute()
    # 20.7.2026: API uz odmita automaticke odeslani ke kontrole
    # ("Changes cannot be sent for review automatically") a vyzaduje
    # changesNotSentForReview=True. Driv to bylo PRESNE NAOPAK (tenhle parametr
    # hazel 400 "must not be set") - chovani se zmenilo, kdyz se appka dostala
    # do zamitnuteho stavu. Odeslani ke kontrole se proto odklepne rucne
    # v Play Console: Prehled publikovani -> Odeslat zmeny ke kontrole.
    edits.commit(packageName=PKG, editId=edit_id,
                 changesNotSentForReview=True).execute()
    print(f"COMMIT OK — v{vc} je v produkcnim tracku, ale JESTE NEODESLANY.")
    print("Dokonci v Play Console: Prehled publikovani -> Odeslat zmeny ke kontrole.")

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "screenshots":
        upload_screenshots()
    elif cmd == "aab":
        upload_aab("--confirm" in sys.argv)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()

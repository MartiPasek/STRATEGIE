#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nahraje snimky obrazovek do Google Play pres Developer API (androidpublisher v3).
Servisni ucet klic: APP/Mobile/play-api-key.json (gitignored). Plne autonomni (bez file pickeru).
Pouziti:  python scripts/play_api_upload.py screenshots
Do budoucna sem pridat i AAB upload (edits.bundles.upload -> tracks.update).
"""
import os, sys, glob
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = os.path.join(ROOT, "APP", "Mobile", "play-api-key.json")
PKG = "cz.strategie.mobile"
LANG = "cs-CZ"
GFX = os.path.join(ROOT, "docs", "google_play_grafika")
SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]

# imageType -> vzor souboru
UPLOADS = {
    "phoneScreenshots":     sorted(glob.glob(os.path.join(GFX, "play_phone_*.png"))),
    "sevenInchScreenshots": sorted(glob.glob(os.path.join(GFX, "play_tablet_*.png"))),
    "tenInchScreenshots":   sorted(glob.glob(os.path.join(GFX, "play_tablet_*.png"))),
}

def main():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    svc = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    edits = svc.edits()

    print("Otviram edit pro", PKG)
    edit_id = edits.insert(packageName=PKG, body={}).execute()["id"]
    print("  editId =", edit_id)

    for image_type, files in UPLOADS.items():
        if not files:
            print("  (preskoceno, zadne soubory)", image_type); continue
        # smazat stavajici snimky daneho typu
        edits.images().deleteall(packageName=PKG, editId=edit_id, language=LANG, imageType=image_type).execute()
        print(f"  {image_type}: smazano stare, nahravam {len(files)}")
        for f in files:
            media = MediaFileUpload(f, mimetype="image/png")
            edits.images().upload(packageName=PKG, editId=edit_id, language=LANG,
                                  imageType=image_type, media_body=media).execute()
            print("     +", os.path.basename(f))

    # commit: tento ucet posila zmeny ke kontrole automaticky (changesNotSentForReview nelze)
    res = edits.commit(packageName=PKG, editId=edit_id).execute()
    print("COMMIT OK. edit committed:", res.get("id"))
    print("Snimky nahrany + odeslany ke kontrole (spolu s bezici revizi).")

if __name__ == "__main__":
    main()

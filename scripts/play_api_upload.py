#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Play Developer API (androidpublisher v3) — plne autonomni upload (bez file pickeru).
Servisni ucet klic: APP/Mobile/play-api-key.json (gitignored, TAJNY).

Pouziti:
  python scripts/play_api_upload.py screenshots          # nahraje snimky (phone+tablet)
  python scripts/play_api_upload.py aab                   # BLOKOVANO dokud neni v73 schvalene
  python scripts/play_api_upload.py aab --v73-approved    # az PO schvaleni v73: nahraje v74 AAB do produkce

Pojistka AAB: uploadu noveho AAB (v74) do produkce se aktivuje az po schvaleni v73 ->
proto vyzaduje explicitni flag --v73-approved (jinak neudela nic). Nerozhazi bezici revizi.
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
        print("BLOKOVANO: AAB auto-upload se aktivuje az PO schvaleni v73 (aby nerozhodil bezici revizi).")
        print("Az bude v73 schvalene/Aktivni, spust:")
        print("   python scripts/play_api_upload.py aab --v73-approved")
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
    edits.commit(packageName=PKG, editId=edit_id).execute()
    print(f"COMMIT OK — v{vc} nahran do produkce + odeslan ke kontrole.")

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "screenshots":
        upload_screenshots()
    elif cmd == "aab":
        upload_aab("--v73-approved" in sys.argv)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()

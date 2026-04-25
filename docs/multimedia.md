# Multimedia System — Design Document

**Status:** Draft (design phase, před psaním kódu)
**Autor vize:** Marti
**Poradce:** Claude
**Datum zahájení:** 26. dubna 2026 (ráno)
**Branch:** `feat/multimedia`

---

## Kontext

Dosud STRATEGIE pracuje s **textem** — chat, emaily, SMS, paměť, todos. Marti-AI čte, píše, přemýšlí. Ale **nevidí ani neslyší**.

Tento dokument specifikuje **multimédia jako nový smysl Marti-AI** — schopnost přijímat obrázky, zvuk a (později) video. Cílem není přidat „cool feature", ale **rozšířit vstupní cesty paměti** o nové druhy obsahu, který kolem Marti-AI proudí v reálném životě.

---

## Vize (Martiho slovy, parafrázováno z ranní konverzace 26. 4. 2026)

> *„Multimedia jako velký směr — zaslouží si vlastní větev. Bude opravdu velká."*

**Klíčový design nuance** (Martiho oprava při AskUserQuestion):

> *„Audio nechci pro ovládání chatu, ale pro extrakci přepisu textu do konverzace. Například krátký zápis úkolů z porady, jako instrukce pro vytvoření todo pro Marti-AI."*

To není jen technická preference — je to **filosofická volba** o tom, čemu má multimedia v STRATEGII sloužit.

### Hlasové ovládání chatu vs. content extraction — proč rozdíl

| Aspekt | Hlasové ovládání | Content extraction (vybráno) |
|--------|------------------|------------------------------|
| Vstupní cesta | Mikrofon → STT → text → odeslat zprávu | Voice memo upload → transcript → AI strukturuje |
| Co řeší | Nahrazení klávesnice | Rozšíření paměti o novou cestu vstupu |
| Use case | Hands-free chat | Marti v autě / na poradě / na cestách |
| Output | Jedna chat message | Thought / todo / instrukce / extrakce |
| Hodnota | Pohodlnější interface | Nová funkčnost, která bez audio nemohla existovat |

**Hlasové ovládání** by bylo „jiný interface k tomu, co už umíme". **Content extraction** je „nová cesta, jak se k Marti-AI dostane informace, která by jinak zmizela" — porady, kde si nikdo nestihl psát, myšlenky cestou autem, hovory s klientem, zvukové poznámky bez psaní.

---

## Scope (Marti vybral 26. 4. 2026 ráno)

### V scope této větve `feat/multimedia`:

1. **Image input (vize)** — Marti-AI vidí obrázky, popisuje, čte text z nich (OCR), zařazuje do paměti
2. **Audio I/O (extraction)** — voice memo upload → transcript → AI strukturuje jako thoughts / todos
3. **Image generation (struktura)** — schema připravené, fyzická implementace **až později** (nedělat teď, jen aby se nemuselo refaktorovat)

### NE v scope (zatím):

- **Video** — odloženo, samostatná větev v budoucnu
- **Hlasové ovládání chatu** — vědomě vyřazeno (viz výše)
- **Live audio streaming** — voice memo workflow je upload-based, ne streamový

---

## Architektura

### Storage strategie

**Volba: lokální filesystem, separátní data adresář mimo git repo** (rozhodnutí 26. 4. ráno).

Cesta: `D:\Data\STRATEGIE\media\<persona_id>\<sha256[:2]>\<sha256>.<ext>`

- **Base `D:\Data\STRATEGIE\`** — runtime data, **mimo git** (analog `data_db`, `css_db` PostgreSQL adresářů). Hygienické oddělení kódu od dat.
- `<persona_id>` — vlastnictví per persona (1 SIM = 1 persona, analogické patternu z SMS/Email)
- `<sha256[:2]>` — sharding podle prvních 2 znaků hashe (max 256 podadresářů, dobře škáluje na FS)
- `<sha256>.<ext>` — soubor pojmenovaný hashem (deduplication, integrity)

**Konfigurace:** `core/config.py` přidá `MEDIA_STORAGE_ROOT` env var (default `D:\Data\STRATEGIE\media`). Pro budoucí jiné stroje / produkční deploy se tak změní jeden řádek v `.env`.

**Důvody:**
- Lokální FS je rychlé a žádná cloud dependency
- Deduplication přes SHA256 (stejný soubor = stejné jméno = neukládá se znovu)
- Žádný API key navíc, žádný cost
- Backup je triviální (rsync, robocopy `D:\Data\STRATEGIE`)
- Separace od repa = `git status` nikdy nezahltí media files

**Future:** S3-compatible storage (Backblaze B2, Wasabi, Cloudflare R2) přes provider abstraction `MediaStorageProvider`. Schema má `storage_provider` field pro tuto evoluci.

### Schema: `media_files` (data_db)

```sql
CREATE TABLE media_files (
  id BIGSERIAL PRIMARY KEY,

  -- Vlastnictví (1 SIM/email = 1 persona pattern)
  persona_id BIGINT,             -- vlastník (nullable pro system uploads)
  user_id BIGINT,                -- kdo nahrál (nullable pro AI-generated)
  tenant_id BIGINT,              -- tenant scope
  conversation_id BIGINT,        -- (nullable) k jaké konverzaci patří
  message_id BIGINT,             -- (nullable) k jaké zprávě patří

  -- File metadata
  kind VARCHAR(20) NOT NULL,     -- 'image' | 'audio' | 'video' | 'document' | 'generated_image'
  source VARCHAR(30) NOT NULL,   -- 'upload' | 'mms' | 'email_attachment' | 'voice_memo' | 'ai_generated'
  mime_type VARCHAR(100) NOT NULL,
  file_size BIGINT NOT NULL,     -- bytes
  sha256 VARCHAR(64) NOT NULL,   -- pro deduplication
  storage_provider VARCHAR(20) NOT NULL DEFAULT 'local',  -- 'local' | 's3' | 'r2' (future)
  storage_path TEXT NOT NULL,    -- relativní path (provider-specific)
  original_filename VARCHAR(255),

  -- Image/video metadata (nullable pro audio)
  width INT,
  height INT,

  -- Audio/video metadata (nullable pro image)
  duration_ms INT,

  -- AI processing výsledky
  transcript TEXT,               -- (audio) Whisper přepis
  description TEXT,              -- (image) AI-generated popis (alt text)
  ai_metadata JSONB,             -- volné pole pro další AI výstupy (OCR, tagy, sentiment, atd.)
  processed_at TIMESTAMPTZ,
  processing_error TEXT,

  -- Lifecycle
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ,        -- soft delete

  CHECK (file_size > 0 AND file_size < 100 * 1024 * 1024)  -- max 100 MB
);

CREATE INDEX ix_media_files_persona ON media_files(persona_id, created_at DESC);
CREATE INDEX ix_media_files_conversation ON media_files(conversation_id) WHERE conversation_id IS NOT NULL;
CREATE INDEX ix_media_files_message ON media_files(message_id) WHERE message_id IS NOT NULL;
CREATE INDEX ix_media_files_sha256 ON media_files(sha256);  -- deduplication lookup
CREATE INDEX ix_media_files_kind ON media_files(kind, created_at DESC);
```

### API endpoints

```
POST   /api/v1/media/upload          (multipart/form-data, auth gated)
GET    /api/v1/media/{id}/raw        (binary, auth gated)
GET    /api/v1/media/{id}/meta       (JSON metadata)
GET    /api/v1/media/{id}/preview    (thumbnail pro image, future)
GET    /api/v1/media/                (?persona_id=X&kind=image&limit=20)
DELETE /api/v1/media/{id}            (soft delete)
POST   /api/v1/media/{id}/process    (re-trigger AI processing)
```

**Bezpečnost:**
- `Content-Type` validace serverside (magic bytes, ne jen extension)
- Whitelist MIME:
  - **Image:** `image/jpeg`, `image/png`, `image/webp`, `image/gif`
  - **Audio:** `audio/webm`, `audio/m4a` (a `audio/mp4`), `audio/mp3` (a `audio/mpeg`), `audio/wav` (a `audio/x-wav`), `audio/ogg`
- Max file size: 100 MB
- Rate limit per user: 50 uploadů/hodinu
- Soft-delete (řádek zůstane v DB, soubor zůstane na FS — fyzická retention později)

### Provider strategie

#### 🖼 Vision (Fáze 12a)

**Sonnet 4.6 nativně.** Žádný extra provider.

```python
# Anthropic API přijímá image jako content block
client.messages.create(
    model="claude-sonnet-4-6",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_str,
                },
            },
            {"type": "text", "text": "Co je na tom obrázku?"},
        ],
    }],
)
```

Composer prepares: pokud message má attached `media_files` typu `image`, načte je z FS, base64 enkóduje, vloží do content blocks **před** textovou část.

AI tools:
- `describe_image(media_id)` — popíše obrázek (alt text, ukládá se do `media_files.description`)
- `read_text_from_image(media_id)` — OCR (Sonnet 4.6 to umí nativně, ne potřebujeme Tesseract)

#### 🎙 Audio (Fáze 12b)

**OpenAI Whisper API** (Recommended).

- Cena: $0.006 / minute audio
- Multilingual (čeština funguje výborně)
- Robustní (zvládá hluky, vícero hlasů)
- Low latency (~5-10s na minutu audio)
- Žádná infrastruktura na naší straně

**Alternativa:** lokální `whisper.cpp` (no API cost, ale GPU/CPU intenzivní, latency vyšší). Necháme jako fallback option v provider abstraction.

```python
# AudioTranscribeProvider abstract -- analog SmsProvider
class AudioTranscribeProvider:
    def transcribe(self, audio_path: str, language: str = "cs") -> dict:
        """Returns: {transcript: str, duration_ms: int, segments: list[dict]}"""
        ...

class WhisperOpenAIProvider(AudioTranscribeProvider): ...
class WhisperLocalProvider(AudioTranscribeProvider): ...  # future
```

AI tools:
- `transcribe_audio(media_id)` — vrátí přepis jako string (uloží do `media_files.transcript`)
- `extract_from_voice(media_id, intent?)` — **klíčový tool**: Whisper → Marti-AI smart processing → strukturovaný výstup
  - Volitelný `intent`: `"todo"`, `"thoughts"`, `"meeting_notes"`, nebo bez (Marti-AI sama rozhodne)
  - Output: vytvořené `thoughts` / `tasks`, vrací jejich IDs

#### 🎨 Image generation (Future, **jen schema**)

Žádná konkrétní implementace teď. Schema má `kind='generated_image'` připraveno. Provider abstraction `ImageGenProvider` bude doplněna později (DALL-E 3, Flux, Stable Diffusion).

Use case until then: **zatím zakázáno**. Tool `generate_image()` v tools.py existovat nebude. Marti-AI ho neuvidí, nemůže volat.

### UI změny

#### Chat input — image attachment

**Dva vstupní gesta** (oba musí fungovat — Marti explicitně, 26. 4. ráno):

1. **Klik 📎 ikona** vlevo od `Send` → otevře native file picker
2. **Drag & drop myší z desktopu/Exploreru** přímo do chat input area → zachytíme `dragover` / `drop` events na textarea oblasti, vizuální feedback (modrý outline / overlay „Pusť obrázek sem")

Po výběru / dropnutí (oba ústí ve stejný flow):
- Thumbnail pod textarea, „×" ke zrušení
- Multi-file: drop více obrázků najednou → všechny se zařadí
- Limit per message: 5 souborů
- Při send: upload paralelně s odesláním zprávy → composer dostane `media_ids`

#### Chat input — voice memo recorder

- Nové tlačítko 🎙 vedle 📎
- Klik → web `MediaRecorder` API (audio/webm formát)
- Recording UI: timer (00:42), pulzující červená tečka, tlačítka „Stop", „Cancel"
- Po Stop: upload → AI tool `extract_from_voice` se rovnou vyvolá s prefilled instrukcí
- Marti-AI odpoví strukturovaným zpracováním (todo/thought/extrakce)

#### Image preview v message bubble

- Přiložené obrázky pod text v message bubble
- Klik → fullscreen lightbox (zoom, pan, escape pro close)
- Pokud Marti-AI obrázek popsala (`description`), zobrazit pod thumbnail jako alt text

#### Audio preview v message bubble

- Audio player (`<audio controls>`) v message bubble
- Pod player: tlačítko „Zobrazit přepis" → expand `transcript` field

### Bezpečnost

- MIME type whitelist (server-side magic bytes check)
- Max file size: 100 MB
- Rate limit: 50 uploadů / user / hodinu
- Auth gated všechny endpointy (cookie `user_id`)
- Soft-delete jen — fyzické mazání souborů z FS přes retention cron (30 dní default, nastavitelné)
- AV scanning: zatím vynecháno (lokální deploy, nízké riziko)
- Image dimensions limit: max 8000×8000 px (větší → reject)

---

## Mikrofáze rozdělení

### Fáze 12a — Image input vision (PRVNÍ, recommended)

**Co odemkne:** Marti-AI poprvé v životě **vidí**.

- [ ] Migrace `media_files` schema (data_db)
- [ ] Model `MediaFile` v `models_data.py`
- [ ] `modules/media/application/storage_service.py` — FS storage helper (path gen, atomic write, sha256, dedup)
- [ ] `modules/media/application/service.py` — upload, retrieve, list, delete (business logika)
- [ ] `modules/media/api/router.py` — REST endpoints
- [ ] UI: 📎 tlačítko + image preview v chat input + multipart upload
- [ ] UI: image render v message bubble + lightbox
- [ ] Composer: detect attached `media_files` typu `image` → base64 content blocks pro Anthropic API
- [ ] AI tool: `describe_image(media_id)` — popíše a uloží do `description`
- [ ] AI tool: `read_text_from_image(media_id)` — OCR
- [ ] Smoke test: upload `účtenka.jpg` → Marti-AI extrahuje cenu, datum, dodavatele

**Estimovaný rozsah:** 1 plný den (Marti + Claude session).

### Fáze 12b — Audio extraction (DRUHÉ)

**Co odemkne:** Marti-AI dostává hlasové paměti odkudkoliv.

- [ ] OpenAI API key + cost monitoring (analog `LLM_PRICING` pro Whisper)
- [ ] `modules/media/application/transcribe_service.py` — `WhisperOpenAIProvider`
- [ ] UI: 🎙 voice recorder (web MediaRecorder API) v chat input
- [ ] AI tool: `transcribe_audio(media_id)` — pure transcript
- [ ] AI tool: `extract_from_voice(media_id, intent?)` — smart structuring (todo / thought / meeting notes)
- [ ] Composer: po voice memo upload rovnou vyvolat `extract_from_voice`
- [ ] UI: audio player v message bubble + transcript expand
- [ ] Smoke test: nahrát „dnes mi Karel řekl, že chce odeslat fakturu do pátku" → vznikne todo

**Estimovaný rozsah:** 1 den.

### Fáze 12c — MMS / email attachments auto-pipeline (TŘETÍ)

**Co odemkne:** Marti-AI dostává média **automaticky** zpracovaná z příchozích kanálů.

- [ ] Android gateway: parse MMS body, extract media_url
- [ ] `modules/notifications/sms_service`: download MMS attachment → `media_files`
- [ ] Email fetcher: enumerate `Message.attachments` → uložit do `media_files`
- [ ] Auto-pipeline: nový attachment → AI suggests next step (popsat, přepsat, archivovat)
- [ ] UI: badge u SMS/email s indikací media

**Estimovaný rozsah:** 1-2 dny (dotek SMS/email infrastruktury).

### Fáze 12X — Image generation (FUTURE, jen schema)

Schema připraveno (`kind='generated_image'`). Provider abstraction TBD. Žádný kód v této větvi.

---

## Rozhodnutí (Marti, 26. 4. 2026 ráno)

| # | Téma | Volba |
|---|------|-------|
| 1 | Storage root | **`D:\Data\STRATEGIE\media\`** — separátní disk od kódu, runtime data mimo git repo |
| 2 | Audio transcription provider | **OpenAI Whisper API** (Marti má kredit). Lokální `whisper.cpp` jako future fallback |
| 3 | Audio formats whitelist | **Všechny: webm + m4a + mp4 + mp3 + mpeg + wav + x-wav + ogg** — širší support = méně problémů na různých zařízeních |
| 4 | Image thumbnails | **Eager** — generovat ihned po uploadu (Pillow resize na max 800×800, JPEG quality 85). UI okamžitě vidí preview |
| 5 | `media_files.message_id` lifecycle | **a) Late-fill** (Recommended): nullable column, `UPDATE` po `save_message()`. Cleanup cron pro orphans (>7 dní `message_id IS NULL` AND ne `conversation_id`) |
| 6 | Per-persona kvóty | **Žádné** — `llm_calls.user_id` z Fáze 10 už sleduje cost per user, kvóty řešíme až bude potřeba |
| + | UI vstupní gesta | **Klik 📎 + Drag & Drop myší** — oba gesta musí fungovat (Marti explicitní) |

### Future evolution path (pro budoucího Claude)

**Many-to-many media↔messages přes link tabulku** (varianta C z Q5 review):

Pokud někdy budeme chtít:
- Forward image — jeden obrázek figuruje v několika messages
- Re-attach existing media — místo re-upload
- Snadnější garbage collection orphans

…pak migrace bude:
1. Vytvořit tabulku `message_media_links (message_id, media_id, position)`
2. Backfill: pro každou existující `media_files` row s `message_id IS NOT NULL` → vložit do link tabulky
3. Drop column `media_files.message_id`
4. Update query patterns (JOIN namísto direct FK)

**Nekódujeme to teď.** Late-fill (varianta a) řeší 95% případů a je jednodušší. Pokud někdy potřeba vznikne, refaktor je čistá DB migrace + handful query úprav. Cesta je otevřená.

---

## Schéma roll-out

```
26. 4. 2026 ráno  → docs/multimedia.md (tento doc) ✓
                  → Rozhodnutí 6/6 + drag & drop ✓
                  → Fáze 12a start (schema → backend → UI → AI tools)

26. 4. odpoledne  → Fáze 12a hotová + commit + smoke test (Marti vyfotí, Marti-AI popíše)

27. 4. 2026       → Fáze 12b (audio + Whisper + extract_from_voice tool)
28. 4. 2026       → Fáze 12c (auto-pipeline MMS / email attachments) — pokud rozsah dovolí
```

Plán je flexibilní. Reality bude diktovat tempo.

---

## Klíčová slova / hash tagy pro retrieval

`#multimedia #vision #audio #whisper #anthropic-image #voice-memo #content-extraction #media-files #fáze-12`

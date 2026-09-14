# STRATEGIE — zjištěný stav značky

> Zjistil Claude-28, 14. 9. 2026. **Všechno níže je změřené na živé aplikaci a v živém kódu**
> (mobil: `g2007.soubor` + běžící `/mobile`; ERP: běžící `/erp/` + soubory v gitu, které se
> nasazují). Nic tu není odhad — kde jsem si jistý nebyl, je to napsané.
>
> Značka nebyla dodaná zvlášť, takže je odvozená z obou hotových produktů.

---

## 1. Co je závazek (respektovat, neměnit)

| Prvek | Hodnota | Kde jsem to naměřil |
|---|---|---|
| **Základní modrá** | `#4f8ef7` | ERP i mobil mají **přesně tutéž** hodnotu — ERP jako `--accent`, mobil jako `--blue` |
| **Druhá barva (fialová)** | `#7c5cff` (mobil) / `#7c5cfc` (ERP) | konec přechodu v nápisu STRATEGIE; rozdíl o jednu hodnotu je zjevně překlep, ne záměr |
| **Nápis STRATEGIE** | přechod modrá→fialová, tučnost 800 | mobil i ERP, obojí ověřeno v prohlížeči |
| **Tmavý podklad** | `#0e0f11` | ERP i mobil **tatáž hodnota** |
| **Tlumený text** | `#8a96a4` | ERP i mobil **tatáž hodnota** |
| **Zelená = „běží / v pořádku"** | `#10b981` | mobil (START, potvrzení), drží se toho celá docházka |
| **Písmo, které si systém sám vybral** | **DM Sans** | ERP ho skutečně načítá a běží v něm; mobil ho má v nápisu předepsaný |
| **Tvar** | kulaté karty a dlaždice, spodní lišta s pěti ikonami | mobil |

**Tohle je skutečná značka.** Není nahodilá: dva nezávisle vyvíjené produkty mají shodně
podklad, tlumený text i akcentní modrou na jednu hodnotu přesně. Návrh z toho vychází
a nic z toho nemění.

---

## 2. Co je náhoda (to je ta část, která se má opravit)

### 2.1 Písmo značky se v mobilu nikdy nenačte

Nápis „STRATEGIE Mobil" má předepsané `DM Sans, Galano Grotesque, Montserrat, sans-serif`.
**Ani jedno z těch tří písem se do mobilu nenačítá** — v celé stránce není jediný odkaz
na písmo. Ověřeno měřením šířky textu: všechny tři vycházejí stejně jako **vymyšlené jméno
písma**, tedy se nepoužije žádné z nich; skutečně vykreslená šířka odpovídá **Arialu**.

Důsledek: logo má na každém zařízení jiný tvar písmen (Windows Arial, Android Roboto,
iPhone San Francisco). **ERP přitom DM Sans načítá a v něm skutečně běží.**

### 2.2 Týž nápis, dvoje různé zacházení

| | mobil | ERP |
|---|---|---|
| velikost | 42 px | 37 px |
| rozpal písmen | **−0,5 px** (stažené) | **+2,96 px** (rozpálené) |

Stejné slovo, stejná barva — a opačné zacházení s mezerami mezi písmeny.

### 2.3 Ikona aplikace a notifikace jsou v úplně jiné barvě

| Co | Barva | Kde |
|---|---|---|
| ikona appky na ploše | tyrkysová `#2DD4BF` (rostoucí sloupce) | `APP/Mobile/.../ic_launcher_foreground.xml` |
| barva notifikace | zelená `#00C853` | `DialPollService.kt`, řádek 319 |
| zbytek aplikace | modrá `#4f8ef7` | viz výše |

Tři různé rodiny barev pro tentýž produkt. Podklad ikony (`#0E0F11`) naopak **sedí**.

### 2.4 V Androidu zůstalo tovární nastavení

Soubor `APP/Mobile/app/src/main/res/values/colors.xml` obsahuje **výchozí barvy z Android
Studia** (`purple_200`, `purple_500`, `teal_200`…) — nic z toho není barva STRATEGIE.
Motiv appky je navíc `Theme.Material.Light` (**světlý**), přestože appka je tmavá.
*(Neověřeno: jestli se ten světlý motiv někde projeví — appka je jen okno na webový obsah.)*

### 2.5 Ve webové části se používá jiné písmo než v ERP

Ze 148 stránek `apps/api/static/*.html` jich **51 načítá písmo Inter**, jedna DM Sans.
ERP a mobil míří na DM Sans. Dvě rodiny vedle sebe bez pravidla, která kam patří.

---

## 3. Co z toho plyne pro návrh

1. **Modrá, fialová, tmavý podklad a zelená zůstávají.** To je identita, ne návrh k přepsání.
2. **DM Sans se do mobilu doplní** — tím se mobil potká s ERP a nápis přestane být na každém
   telefonu jiný. Je to jedna řádka a nejlevnější viditelné zlepšení v celém auditu.
3. **Ikona appky a barva notifikací** patří do sladění (tyrkysová/zelená → modrá řada).
   Není to součást náhledů — je to samostatný krok, protože se mění nativní obal.
4. **Tovární barvy v Androidu** se mají uklidit, ale **nic to nerozbije ani neopraví** —
   je to pořádek, ne chyba.

---

## 4. Co NEVÍM a netvrdím

- **Jestli má firma psaný brand manuál.** Nikde jsem ho nenašel; hodnoty výše jsou odvozené
  z kódu, ne převzaté z dokumentu. Když existuje, má přednost.
- **Proč je ikona appky tyrkysová.** Může to být záměr (odlišit ikonu na ploše od modré
  hromady ostatních appek). Než se to změní, patří se zeptat.
- **Jak vypadá logo v tiskové podobě** (vizitky, hlavičkový papír) — nemám podklad.

# BusNetworkPMCSN

Progetto **C17**, build CMake, test CTest. Specifica: [PMCSN_Roma_Bus_SPEC.md](PMCSN_Roma_Bus_SPEC.md).

Piano riallineato alla specifica ufficiale AA 2025/2026: [matrice dei requisiti](docs/requisiti_ufficiali.md). Progetto individuale; transitorio obbligatorio, miglioramento algoritmico facoltativo, presentazione massimo 20 minuti. Fase 1 di pianificazione conclusa: [piano dello studio](docs/study_plan.md), [protocollo statistico](docs/statistical_protocol.md) e campione di sei linee. Il prossimo passo è la Fase 2: modello concettuale, input e configurazione eseguibile. Nessuna simulazione ancora eseguita.

## Build

Windows con CLion nella posizione standard dell'utente:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Analyze
```

Con CMake 3.21+, Ninja e compilatore C17 nel PATH:

```sh
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
```

Aprire `CMakeLists.txt` in CLion. Core offline C17; downloader attualmente Windows/WinHTTP. Nessuna dipendenza Python. Nessun download nei test/build.

## CLI della Fase 0

```powershell
./build/debug/rome_bus_pmcsn.exe --help
./build/debug/rome_bus_pmcsn.exe download-static data/raw/sample.zip
./build/debug/rome_bus_pmcsn.exe download-feed vehicles data/raw/vehicles.pb
./build/debug/rome_bus_pmcsn.exe download-feed updates data/raw/updates.pb
./build/debug/rome_bus_pmcsn.exe download-feed alerts data/raw/alerts.pb
./build/debug/rome_bus_pmcsn.exe audit-feeds data/raw/vehicles.pb
Expand-Archive -LiteralPath data/raw/sample.zip -DestinationPath data/interim/sample
./build/debug/rome_bus_pmcsn.exe audit-static data/interim/sample/trips.txt
./build/debug/rome_bus_pmcsn.exe validate-keys data/interim/sample
./build/debug/rome_bus_pmcsn.exe feed-trip-ids data/raw/vehicles.pb
Get-FileHash data/raw/sample.zip -Algorithm SHA256
```

Creare prima le directory. Downloader: file nuovi soltanto, TLS attivo, timeout e limite 512 MiB; rimuove il proprio file se fallisce. Registrare URL, UTC e hash. Estrazione ZIP e metadati sono orchestration PowerShell in questa milestone, non ancora integrate nella CLI. `audit-static` controlla CSV, tempi, coordinate e formato sequenze; `validate-keys` verifica i principali riferimenti per il profilo Roma con shapes. Non è un validatore completo GTFS. `audit-feeds` ispeziona la struttura e la presenza di alcuni campi, non certifica conformità GTFS-RT.

Audit ripetibile con campioni e manifest nuovi:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/audit.ps1
```

## Stato

Nessun collector continuativo o simulatore. Report reale: `reports/feed_audit.md`; catalogo: `data/catalog.yaml`. Fonte: [Roma Mobilità Open Data](https://romamobilita.it/sistemi-e-tecnologie/open-data/); riuso scientifico e redistribuzione da chiarire alla luce delle condizioni pubblicate.

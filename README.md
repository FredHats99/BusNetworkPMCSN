# BusNetworkPMCSN

Fase 3 conclusa nel perimetro sintetico dichiarato: dal 2026-10-28 anche la rete
usa **Lehmer a=48271, m=2147483647**, come nelle lezioni 16/17 del corso.
[Gate 3.8 Lehmer v2.0 accettato](reports/gate38_results.md): 8064 nuove repliche,
8904 asserti superati, nessun fallimento o inconcludente; tutti gli obiettivi
di precisione raggiunti con margini e inventario invariati.

[Piano congelato](docs/lehmer_migration.md), [audit e budget residui](reports/lehmer_migration.md),
[implementazione e comandi](docs/phase3_implementation.md).
La conferma consuma una parte consistente del periodo finito di Lehmer:
prima degli esperimenti successivi occorre dimensionare i consumi sui blocchi
residui. La disgiunzione delle sequenze non prova indipendenza statistica.

Le evidenze MRG32k3a del 2026-10-22 sono [conservate separatamente](reports/mrg32k3a_v1_1/README.md);
nessun pooling con il nuovo campione. Nessuna validazione empirica di domanda/OD/tempi reali.

Fase 4 completata il 2026-10-29: [studio del transitorio](reports/transient_analysis.md),
192 repliche, grafici, tabelle e [basi accademiche del corso](docs/phase4_academic_basis.md).
Studio finito 07:00-11:00, warm-up zero; accumulo e sensibilita iniziale persistente
negli scenari ad alta domanda. Nessun regime stazionario certificato.
Il successivo confronto principale e' condizionato allo stato vuoto; il caricato
resta sensibilita separata. Pilota e produzione di Fase 5 ancora da eseguire.
[Protocollo del runner](docs/phase4_protocol.md), [piano e riserve](reports/phase4_plan.md),
[audit di completamento](reports/phase4_completion.json).

Fase 2 conclusa come specifica il 2026-10-22:
[contratto operativo e riproduzione](docs/phase2_operational_contract.md),
[input GTFS e sintetici](docs/phase2_inputs.md).

Progetto **C17**, build CMake, test CTest. Specifica: [PMCSN_Roma_Bus_SPEC.md](PMCSN_Roma_Bus_SPEC.md).

Piano riallineato alla specifica ufficiale AA 2025/2026: [matrice dei requisiti](docs/requisiti_ufficiali.md). Progetto individuale; transitorio obbligatorio, miglioramento algoritmico facoltativo, presentazione massimo 20 minuti. Fasi 1–2 concluse come pianificazione e specifica: [piano dello studio](docs/study_plan.md), [protocollo statistico](docs/statistical_protocol.md) e campione di sei linee. Stato dei gate di Fase 3 nel documento di implementazione.

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

Simulatore offline: `simulate controlled`, `simulate network`, `validate controlled`
e `validate network`. Input con `python scripts/export_simulation.py`; verifiche
estese con `python scripts/verify_controlled.py` e `python scripts/verify_network.py`.
Nessun collector continuativo. Report reale: `reports/feed_audit.md`; catalogo: `data/catalog.yaml`. Fonte: [Roma Mobilità Open Data](https://romamobilita.it/sistemi-e-tecnologie/open-data/); riuso scientifico e redistribuzione da chiarire alla luce delle condizioni pubblicate.

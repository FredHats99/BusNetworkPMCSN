# Gate 3.8 — conferma indipendente, versione 1.1

Data: 2026-10-22. Esecuzione autorizzata dall'utente dopo la proposta di 672 nuove
repliche per ciascuno dei dodici casi. Criteri in `configs/gate38_confirmation.json`.
La versione 1.0 e tutti i suoi risultati rimangono conservati.

Si mantengono esattamente: input, popolazione, 413 archi, 15 gruppi aggregati,
8904 asserti, margini ±0.02/±0.03/±0.03/±10 s, quantili CDF, regole di copertura,
confronti e IC Student bilaterali con Bonferroni simultanei nominali al 95%.
La validità resta approssimata per statistiche non normali. Le definizioni e le
limitazioni scientifiche sono quelle di `docs/gate38_protocol.md`.

Le 384 repliche v1 servono solo a diagnosi e pianificazione. Gli IC decisionali
v1.1 usano soltanto **672 nuove repliche per caso**, 8064 totali. L'obiettivo di
precisione pianificato è semiampiezza non superiore a metà del rispettivo margine.
Il massimo sulle dispersioni v1 richiede indicativamente 670 repliche: si fissa
672 prima delle nuove osservazioni. Il risultato non è garantito dalla stima
di dispersione, e questa precisione non garantisce equivalenza vicino al margine.

`reports/gate38_confirmation_plan.json` conserva dimensionamento, hash dei dati
di pianificazione e scomposizione descrittiva dei dieci casi critici, con riusi,
chiavi nuove e bin. Nessun loro dato viene incorporato nella decisione finale.

La radice resta 123456789. Il prefisso scartato in ciascuno degli stream 0–3 è la
prima potenza di due strettamente superiore al massimo consumo finale della v1,
registrato nei criteri prima dell'avvio. Il runner verifica gli hash e la
disgiunzione. Gli stati continuano fra tutte le nuove repliche e tutti gli scenari.
La v1 non viene ripetuta con un nuovo nome di directory né accodata agli IC.

Si esegue l'intero inventario, senza selezionare soltanto gli asserti inconcludenti.
Nessun arresto o cambiamento di N in base agli esiti, nessun allargamento dei
margini, nessuna estensione automatica successiva. Ogni controllo può risultare
superato, non superato o inconcludente. Solo il superamento di tutti i requisiti
esatti e di tutti gli asserti obbligatori accetta il gate nel perimetro dichiarato.

Per il costo di esecuzione si usa una tabella hash per la sola ricerca dei fattori
memoizzati, senza modificare creazione, ordine, indici o RNG. Dodici casi prima/dopo
producono JSONL e CSV identici; la build Release con `-O2 -DNDEBUG -fno-builtin`
conserva la stessa equivalenza. Una build Release sperimentale con built-in matematici
produceva tre differenze di un ulp nelle tracce ed è stata scartata per la conferma.
L'analisi legge i riepiloghi in streaming e conserva statistiche di replica in
colonne numeriche; le formule inferenziali rimangono identiche. Il confronto
degli esiti v1 prima/dopo è un prerequisito prima della conferma.

Comando di raccolta e analisi:

```powershell
python scripts/gate38.py --criteria configs/gate38_confirmation.json --exe build/release/rome_bus_pmcsn.exe --output-dir data/processed/phase3/gate38_confirmation_v1_1
```

Tutti i dati grezzi e gli hash sono conservati. Una diagnosi con maggiore
precisione non calibra i dati sintetici, non conclude il transitorio e non
sostituisce il pilota/produzione statistico della Fase 5.

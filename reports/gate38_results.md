# Gate 3.8 — diagnostica e criteri di accettazione

Esito della versione 1.1: **accettato**.

Eseguite 8064 repliche: 672 per ognuno dei sei scenari e dei due stati iniziali. Non sono il pilota o la produzione. Gli stream sono continuati anche fra scenari, dopo il prefisso disgiunto delle prove precedenti.

Requisiti esatti e prerequisiti software: **superati**. Ogni ingresso nel tratto, anche con arrivo dopo le 11, è stato verificato contro gli input, le chiavi ambientali, i riusi, i consumi RNG e lo stato finale dei bus.

Inventario fissato prima delle run: 413 archi nominali, 15 gruppi aggregati, 8904 asserti. IC Student bilaterali con Bonferroni, confidenza simultanea nominale 95%; copertura approssimata per output non normali.

## Esiti obbligatori

| Famiglia | Superati | Non superati | Inconcludenti |
|---|---:|---:|---:|
| comparison_arc_time | 2478 | 0 | 0 |
| comparison_marginal | 420 | 0 | 0 |
| reference_arc_time | 4956 | 0 | 0 |
| reference_marginal | 1050 | 0 | 0 |

Totale: 8904 superati, 0 non superati, 0 inconcludenti.

Un IC interamente entro il margine accetta l'equivalenza operativa; interamente fuori la respinge; un IC a cavallo del limite lascia il controllo inconcludente. Nessun margine o numero di repliche è stato adattato agli esiti.

Inconcludenti per precisione: 0; per copertura incompleta: 0.

## Marginali aggregate: rete, linea/direzione e dominio

I fattori sono valutati contro media 1, CV 0.2 e CDF ai quantili 0.10/0.25/0.50/0.75/0.90. Per SHARED–BASE e SHARED_D125–D125 si confrontano anche le differenze delle stesse statistiche. Le tolleranze locali sono ±0.02, ±0.03 e ±0.03 rispettivamente. REGULAR è controllato esattamente e non confrontato sul CV.

| Caso | Media fattore rete | CV rete | Controlli aggregati superati / totali |
|---|---:|---:|---:|
| D075 / empty_passengers | 1 | 0.19988 | 105 / 105 |
| D075 / loaded_synthetic | 0.99992 | 0.19985 | 105 / 105 |
| BASE / empty_passengers | 1.0002 | 0.20007 | 105 / 105 |
| BASE / loaded_synthetic | 0.99991 | 0.1999 | 105 / 105 |
| D125 / empty_passengers | 1 | 0.20004 | 105 / 105 |
| D125 / loaded_synthetic | 0.99997 | 0.19995 | 105 / 105 |
| REGULAR / empty_passengers | 1 | 0 | 0 / 0 |
| REGULAR / loaded_synthetic | 1 | 0 | 0 / 0 |
| SHARED / empty_passengers | 0.99994 | 0.19996 | 105 / 105 |
| SHARED / loaded_synthetic | 1.0001 | 0.2 | 105 / 105 |
| SHARED_D125 / empty_passengers | 1.0001 | 0.19992 | 105 / 105 |
| SHARED_D125 / loaded_synthetic | 1 | 0.19997 | 105 / 105 |

## Archi e tempi medi

Sono obbligatori lo scostamento medio dal riferimento e i confronti BASE–REGULAR, SHARED–BASE, SHARED_D125–D125 sui tempi medi effettivi, con margine ±10 secondi. L'insieme degli archi viene dal calendario, non viene ridotto in base ai passaggi osservati. Un arco assente in una replica non viene imputato a zero.

La media effettiva è scomposta in media del riferimento selezionato più scostamento medio dovuto al fattore. Cambiamenti nei bus che raggiungono un arco entro T possono cambiare anche la composizione dei riferimenti.

| Confronto | Stato iniziale | Superati | Non superati | Inconcludenti |
|---|---|---:|---:|---:|
| BASE–REGULAR | empty_passengers | 413 | 0 | 0 |
| SHARED–BASE | empty_passengers | 413 | 0 | 0 |
| SHARED_D125–D125 | empty_passengers | 413 | 0 | 0 |
| BASE–REGULAR | loaded_synthetic | 413 | 0 | 0 |
| SHARED–BASE | loaded_synthetic | 413 | 0 | 0 |
| SHARED_D125–D125 | loaded_synthetic | 413 | 0 | 0 |

## Esiti bloccanti

Nessuno: tutti gli asserti obbligatori sono superati.

## Diagnostiche supplementari

Nei dati completi sono conservate per replica anche CDF/CV di ogni arco, distribuzione delle sole chiavi nuove, riusi, composizione dei riferimenti e strati per bin ambientale. La verifica inferenziale obbligatoria delle marginali riguarda i gruppi aggregati; a livello di singolo arco è obbligatoria la verifica delle medie in secondi. Non si dichiara equivalenza dell'intera distribuzione su ogni arco.

Totale ingressi nei tratti: 64861684; ingressi con arrivo alle 11 o dopo: 436207. Questi ultimi sono inclusi nelle statistiche dei tempi assegnati.

## Decisione e attività successive

Accettato soltanto entro il perimetro e le tolleranze dichiarate. Prima della produzione restano transitorio, riesame dei confini e orchestrazione della campagna statistica.

## Separazione dalla pianificazione

Questa decisione usa soltanto il campione nuovo. Le 384 repliche v1 sono usate per diagnosi e dimensionamento, non per gli IC finali.
Obiettivi di semiampiezza entro metà margine: 8904 / 8904.
Nessuna estensione automatica della campagna in base all'esito.

Controlli precedentemente inconcludenti ora superati: 634 / 634.
Il caso precedentemente più vicino/oltre soglia, linea 81 direzione 0 70348→83180, passa da una stima diagnostica -10.02191 s a 0.13750 s nel campione indipendente, con IC simultaneo [-3.28417, 3.55916] s, interno al margine ±10 s.
Le stime provengono da campioni separati; i dati di pianificazione non sono stati accodati agli intervalli finali.

La domanda, l'OD e i tempi restano sintetici: questa diagnostica non è validazione empirica del servizio reale.

## Riproduzione e audit

```powershell
python scripts/gate38.py --criteria configs/gate38_confirmation.json --exe build/release/rome_bus_pmcsn.exe --output-dir data/processed/phase3/REPRODUCTION_NEW_DIRECTORY
python scripts/gate38.py --analyze-only data/processed/phase3/gate38_confirmation_v1_1
python scripts/render_gate38_report.py data/processed/phase3/gate38_confirmation_v1_1
```

Una riproduzione richiede una directory nuova (`--output-dir`); il runner non sovrascrive campagne precedenti. Cambiare soltanto directory ripete le stesse sequenze e non aggiunge repliche indipendenti. Una campagna successiva richiede un protocollo versionato e un tratto RNG disgiunto o una continuazione verificata degli stati.
Criteri: `configs/gate38_confirmation.json`; protocollo: `docs/gate38_confirmation_protocol.md`; esito strutturato: `reports/gate38_results.json`; tutti gli asserti: `reports/gate38_assertions.csv`.

SHA256 criteri: `c92c1cdd259c336db5f330809bdfc3d79e10fefa4dc0947ba2ec7cb6b5a1376a`. SHA256 inventario: `d42660d48acae8386463b05d4dd7785740eb3d2a15a7ad886271066a795b4c26`.

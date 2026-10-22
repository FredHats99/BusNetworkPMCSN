# Gate 3.8 — diagnostica e criteri di accettazione

Esito della versione 1.0: **inconcludente**.

Eseguite 384 repliche diagnostiche: 32 per ognuno dei sei scenari e dei due stati iniziali. Non sono il pilota o la produzione. Gli stream sono continuati anche fra scenari, dopo il prefisso disgiunto delle prove precedenti.

Requisiti esatti e prerequisiti software: **superati**. Ogni ingresso nel tratto, anche con arrivo dopo le 11, è stato verificato contro gli input, le chiavi ambientali, i riusi, i consumi RNG e lo stato finale dei bus.

Inventario fissato prima delle run: 413 archi nominali, 15 gruppi aggregati, 8904 asserti. IC Student bilaterali con Bonferroni, confidenza simultanea nominale 95%; copertura approssimata per output non normali.

## Esiti obbligatori

| Famiglia | Superati | Non superati | Inconcludenti |
|---|---:|---:|---:|
| comparison_arc_time | 2137 | 0 | 341 |
| comparison_marginal | 362 | 0 | 58 |
| reference_arc_time | 4728 | 0 | 228 |
| reference_marginal | 1043 | 0 | 7 |

Totale: 8270 superati, 0 non superati, 634 inconcludenti.

Un IC interamente entro il margine accetta l'equivalenza operativa; interamente fuori la respinge; un IC a cavallo del limite lascia il controllo inconcludente. Nessun margine o numero di repliche è stato adattato agli esiti.

Inconcludenti per precisione: 634; per copertura incompleta: 0.

## Marginali aggregate: rete, linea/direzione e dominio

I fattori sono valutati contro media 1, CV 0.2 e CDF ai quantili 0.10/0.25/0.50/0.75/0.90. Per SHARED–BASE e SHARED_D125–D125 si confrontano anche le differenze delle stesse statistiche. Le tolleranze locali sono ±0.02, ±0.03 e ±0.03 rispettivamente. REGULAR è controllato esattamente e non confrontato sul CV.

| Caso | Media fattore rete | CV rete | Controlli aggregati superati / totali |
|---|---:|---:|---:|
| D075 / empty_passengers | 1 | 0.1995 | 104 / 105 |
| D075 / loaded_synthetic | 0.9997 | 0.20006 | 105 / 105 |
| BASE / empty_passengers | 1.0004 | 0.20064 | 103 / 105 |
| BASE / loaded_synthetic | 1.0001 | 0.2004 | 105 / 105 |
| D125 / empty_passengers | 0.9997 | 0.20069 | 105 / 105 |
| D125 / loaded_synthetic | 1.0004 | 0.20025 | 105 / 105 |
| REGULAR / empty_passengers | 1 | 0 | 0 / 0 |
| REGULAR / loaded_synthetic | 1 | 0 | 0 / 0 |
| SHARED / empty_passengers | 0.99984 | 0.19999 | 105 / 105 |
| SHARED / loaded_synthetic | 0.99964 | 0.20008 | 104 / 105 |
| SHARED_D125 / empty_passengers | 1.0002 | 0.19943 | 104 / 105 |
| SHARED_D125 / loaded_synthetic | 0.99978 | 0.20003 | 103 / 105 |

## Archi e tempi medi

Sono obbligatori lo scostamento medio dal riferimento e i confronti BASE–REGULAR, SHARED–BASE, SHARED_D125–D125 sui tempi medi effettivi, con margine ±10 secondi. L'insieme degli archi viene dal calendario, non viene ridotto in base ai passaggi osservati. Un arco assente in una replica non viene imputato a zero.

La media effettiva è scomposta in media del riferimento selezionato più scostamento medio dovuto al fattore. Cambiamenti nei bus che raggiungono un arco entro T possono cambiare anche la composizione dei riferimenti.

| Confronto | Stato iniziale | Superati | Non superati | Inconcludenti |
|---|---|---:|---:|---:|
| BASE–REGULAR | empty_passengers | 391 | 0 | 22 |
| SHARED–BASE | empty_passengers | 335 | 0 | 78 |
| SHARED_D125–D125 | empty_passengers | 337 | 0 | 76 |
| BASE–REGULAR | loaded_synthetic | 390 | 0 | 23 |
| SHARED–BASE | loaded_synthetic | 347 | 0 | 66 |
| SHARED_D125–D125 | loaded_synthetic | 337 | 0 | 76 |

## Esempi dei controlli che impediscono l'accettazione

La tabella seguente mostra fino a 15 casi; il CSV conserva l'intero inventario, compresi gli esiti favorevoli.

| Caso/confronto | Gruppo | Metrica | Deviazione | IC deviazione | Margine | Esito |
|---|---|---|---:|---|---:|---|
| SHARED_D125 / loaded_synthetic − D125 | 81 dir 0: 70348→83180 | mean_duration | -10.022 | [-27.216, 7.1724] | 10.0 | inconcludente |
| SHARED_D125 / empty_passengers − D125 | 81 dir 1: 70549→72066 | mean_duration | 7.7164 | [-7.8571, 23.29] | 10.0 | inconcludente |
| D125 / loaded_synthetic | 81 dir 0: 70348→83180 | mean_delta | 6.3183 | [-6.4087, 19.045] | 10.0 | inconcludente |
| SHARED / empty_passengers − BASE | 81 dir 0: 70747→70517 | mean_duration | -6.2747 | [-23.619, 11.069] | 10.0 | inconcludente |
| D075 / empty_passengers | 81 dir 0: 70747→70517 | mean_delta | 6.1893 | [-12.435, 24.814] | 10.0 | inconcludente |
| SHARED_D125 / empty_passengers − D125 | 628 dir 0: 78133→73225 | mean_duration | -6.1778 | [-21.269, 8.9134] | 10.0 | inconcludente |
| SHARED / empty_passengers − BASE | 87 dir 1: 30946→30784 | mean_duration | -6.1252 | [-23.921, 11.671] | 10.0 | inconcludente |
| SHARED / empty_passengers − BASE | 81 dir 1: 70549→72066 | mean_duration | -5.9208 | [-19.568, 7.7268] | 10.0 | inconcludente |
| SHARED_D125 / loaded_synthetic − D125 | 81 dir 1: 70374→82697 | mean_duration | 5.6671 | [-3.9667, 15.301] | 10.0 | inconcludente |
| SHARED_D125 / empty_passengers | 628 dir 0: 78133→73225 | mean_delta | -5.6479 | [-14.466, 3.1705] | 10.0 | inconcludente |
| SHARED_D125 / empty_passengers − D125 | 628 dir 0: 70515→70517 | mean_duration | 5.5723 | [-11.679, 22.824] | 10.0 | inconcludente |
| SHARED / empty_passengers − BASE | 87 dir 0: 72080→81821 | mean_duration | -5.3734 | [-22.225, 11.479] | 10.0 | inconcludente |
| SHARED_D125 / empty_passengers − D125 | 19BUS dir 0: 71337→71344 | mean_duration | 5.2292 | [-3.0915, 13.55] | 10.0 | inconcludente |
| SHARED / loaded_synthetic − BASE | line / 70 / 0 | cdf_0.5 | 0.015527 | [-0.011202, 0.042255] | 0.03 | inconcludente |
| SHARED / empty_passengers − BASE | 70 dir 1: 70170→78886 | mean_duration | 4.9435 | [-5.7817, 15.669] | 10.0 | inconcludente |

## Diagnostiche supplementari

Nei dati completi sono conservate per replica anche CDF/CV di ogni arco, distribuzione delle sole chiavi nuove, riusi, composizione dei riferimenti e strati per bin ambientale. La verifica inferenziale obbligatoria delle marginali riguarda i gruppi aggregati; a livello di singolo arco è obbligatoria la verifica delle medie in secondi. Non si dichiara equivalenza dell'intera distribuzione su ogni arco.

Totale ingressi nei tratti: 3088942; ingressi con arrivo alle 11 o dopo: 20906. Questi ultimi sono inclusi nelle statistiche dei tempi assegnati.

## Decisione e attività successive

Il gate 3.8 resta aperto. La diagnostica è completa per questo protocollo, ma i requisiti di equivalenza non sono tutti soddisfatti.
Tutti i gruppi obbligatori hanno copertura completa. Gli esiti inconcludenti dipendono dalla precisione: 32 repliche non bastano per alcuni margini con questa correzione simultanea. Occorre pianificare e congelare una nuova campagna indipendente prima di raccogliere altri dati; nessun aumento automatico delle repliche.
Nessun IC obbligatorio è interamente fuori margine: non emerge una violazione conclusiva dei margini, ma questo non dimostra equivalenza. Le medie puntuali oltre soglia con IC ampio non sono da sole prova di un bug.

La domanda, l'OD e i tempi restano sintetici: questa diagnostica non è validazione empirica del servizio reale.

## Riproduzione e audit

```powershell
python scripts/gate38.py
python scripts/gate38.py --analyze-only data/processed/phase3/gate38_v1
python scripts/render_gate38_report.py data/processed/phase3/gate38_v1
```

Una riproduzione richiede una directory nuova (`--output-dir`); il runner non sovrascrive campagne precedenti. Cambiare soltanto directory ripete le stesse sequenze e non aggiunge repliche indipendenti. Una campagna successiva richiede un protocollo versionato e un tratto RNG disgiunto o una continuazione verificata degli stati.
Criteri: `configs/gate38_criteria.json`; protocollo: `docs/gate38_protocol.md`; esito strutturato: `reports/gate38_results.json`; tutti gli asserti: `reports/gate38_assertions.csv`.

SHA256 criteri: `5c385fb135f8a8173124e69490280a6268b61d7b54d7f440d6643ebf0b3c1e2f`. SHA256 inventario: `d42660d48acae8386463b05d4dd7785740eb3d2a15a7ad886271066a795b4c26`.

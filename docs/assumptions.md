# Registro delle ipotesi — chiusura Fase 1, 2026-10-09

Ogni parametro esecutivo di Fase 2 deve riportare unità, fonte, versione, stato
osservato/stimato/assunto/calibrato e incertezza. Nulla è dichiarato calibrato.
"Osservato nel GTFS" significa contenuto del file programmato, non servizio reale.

| Elemento | Stato | Evidenza / scelta | Lavoro successivo |
|---|---|---|---|
| Topologia, sequenze e calendario | Osservati nello snapshot GTFS | Sei linee 81/628/87/70/5BUS/19BUS; servizio 2026-10-12; checksum nell'audit | Specifica del grafo e geometria archi in Fase 2; nessuna validazione operativa completa |
| 260 partenze, 310 stop_id, 15 varianti | Derivati dal GTFS | `reports/network_sample.json` e audit | Non equivalgono a carico, flotte o congestione osservata |
| Finestra 07:00–11:00 | Scelta dello studio | Studio finito; 48 corse già in viaggio, 63 arrivi oltre il termine | Stato iniziale/arresto in Fase 2; orizzonte motivato in Fase 4 |
| FIFO, capacità finita, discese prima delle salite | Assunti nel modello base | Servizio batch mobile pertinente agli obiettivi | Definire dettagli ed eventi; verificare bilanci/capacità |
| Domanda e OD | Assunti, valori assoluti non fissati | Moltiplicatori 0.75/1/1.25 sono scenari locali | Definire profili, destinazioni ammissibili e fonti/plausibilità in Fase 2 |
| Capacità bus e coefficienti dwell | Da assumere o stimare con fonte | Nessun conteggio affidabile già disponibile | Specificare valori, unità e sensibilità; nessuna domanda ricavata dai soli ritardi |
| Tempi di viaggio e variabilità | Da specificare; nessun fit empirico eseguito | Orari programmati disponibili, tutti i passaggi esportati con arrival=departure | Separare travel/dwell e scegliere leggi giustificate senza doppio conteggio |
| Perturbazioni indipendenti/condivise | Ipotesi sperimentale | Stesse leggi marginali, dipendenza fra linee diversa su archi comuni validati | Congelare dominio, distribuzioni e intensità prima delle run; non è congestione causata dai bus |
| Assenza di trasbordi, turni e stalli contesi | Delimitazione assunta | Primo modello gestibile | Non generalizzare conclusioni agli effetti esclusi |
| RNG e seed | Metodo candidato tratto dal libro; non validato in codice | rngs multi-stream e continuazione stati, protocollo dedicato | Gate su implementazione, consumi cumulativi e adeguatezza; sostituire con fonte accademica se insufficiente |
| 40 piloti, 95%, precisione 10 s | Scelte locali di pianificazione | Metodi Leemis–Park 8.1/8.3; N stimato dal pilota, produzione indipendente | Precisione finale da verificare, non garantita dalla numerosità pilota |

Endpoint pubblicati: accessibilità verificata solo nei campioni del catalogo.
Aggiornamento circa 60 s dichiarato dalla fonte, non misurato con storico continuo.
Occupazione qualitativa non equivale a conteggio o domanda misurata.
Riuso scientifico/redistribuzione dei dati non confermati dalle condizioni pubblicate;
nessuna raccolta continuativa richiesta per chiudere la pianificazione.

I risultati delle simulazioni saranno condizionati agli input, non misure di code
reali. IC Monte Carlo e incertezza delle ipotesi sono distinti. Estensione all'intera
rete resta un obiettivo futuro, non una conclusione rappresentativa del campione.

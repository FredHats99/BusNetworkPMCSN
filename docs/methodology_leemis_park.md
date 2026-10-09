# Metodo Leemis–Park: sviluppo del modello e studio

Consultazione: 2026-10-09. Fonte fornita dall'utente:
`C:/Users/feder/Desktop/Discrete Event Simulation - A First Course - Lemmis Park.pdf`.
SHA-256: `53F2A93C7B9764DEAA9B20897EDE39C9C070C527A31818D8E1BFDD3F3BF01280`.

Autori verificati sul frontespizio: Lawrence Leemis e Steve Park.
Il file ha 538 pagine PDF e riporta *Current Revision, December 2004*.
Non è identificato dal frontespizio come l'edizione Pearson 2006 citata nella
consegna. La consegna menziona algoritmi 1.1 e 1.2; qui le due procedure
metodologiche sono Algorithm 1.1.1 e Algorithm 1.1.2. L'associazione è una
corrispondenza di contenuto con sviluppo e conduzione dello studio, non una
verifica bibliografica dell'identità con l'edizione 2006.

Consultate le sezioni 1.1.2 e 1.1.3, pp. 3–7 stampate (PDF 13–17), inclusi
esempio e commenti intermedi. Controllati visivamente frontespizio e pagine PDF
14 e 17. Non si dichiara letto integralmente il libro o il capitolo Output Analysis.
Le descrizioni sotto sono parafrasi, con applicazioni locali separate dalla fonte.

## Algorithm 1.1.1 — sviluppo del modello

Fonte: p. 4 stampata, PDF 14. I passi 2–6 possono essere iterati più volte.

| Passo del testo | Contenuto effettivo | Applicazione a Roma Bus / artefatto | Stato |
|---|---|---|---|
| 1 | Identificato il sistema, determinare obiettivi specifici dell'analisi | Campione 4+2, domande su domanda, regolarità e ambiente comune, criteri decisionali in `study_plan.md` | Obiettivi di Fase 1 consolidati |
| 2 | Costruire il modello concettuale: stato, relazioni, dinamica e dettaglio pertinente agli obiettivi | Passeggeri, bus, code, occupazione, collegamenti e interazioni; separare stato fisico e statistiche. Specificare cosa significa simulare linee insieme | Fase 2, `model_spec.md`, ancora aperta |
| 3 | Convertire il concetto in un modello di specifica; costruire gli input mediante raccolta e analisi dei dati, o modelli stocastici ritenuti rappresentativi quando mancano dati | Calendario e topologia dallo snapshot; domanda/OD, capacità, travel/dwell e inizializzazione con fonti o ipotesi esplicite. Definire leggi e vincoli prima del codice | Fase 2, configurazioni e registro input, ancora aperta |
| 4 | Tradurre la specifica in un modello computazionale, scegliendo linguaggio generale o simulativo | Implementazione DES in C17, scelta già dell'utente; strutture, eventi e metriche devono attuare la specifica | Fase 3, simulatore non implementato |
| 5 | Verificare che il programma implementi correttamente la specifica | Bilanci, limiti di capacità, ordinamento eventi, casi deterministici e controlli delle metriche | Fase 3, non conclusa dall'audit GTFS |
| 6 | Validare che il modello computazionale rappresenti adeguatamente il sistema per lo scopo dell'analisi | Confronti con evidenze disponibili e controlli di plausibilità dichiarati; non validare code reali senza dati indipendenti | Fase 3, validazione ancora da progettare/eseguire |

Il testo distingue verifica e validazione: una risposta corretta alla prima
non dimostra la seconda. L'esempio 1.1.1 (p. 5, PDF 15) discute anche controlli
di consistenza quando manca un sistema operativo da confrontare: sono utili,
ma non autorizzano a chiamare empiricamente validata una domanda bus assunta.

I commenti a p. 7 (PDF 17) indicano di mantenere il modello semplice ma adeguato,
evitando sia dettagli estranei sia omissioni rilevanti. Lo sviluppo reale non
è rigidamente sequenziale; non saltare i primi tre passi per iniziare a programmare.
La proposta di ampliare in futuro la rete non implica inserire subito trasbordi,
turni dei mezzi o contese alle fermate senza obiettivi e input che li giustifichino.

## Algorithm 1.1.2 — conduzione dello studio

Fonte: p. 7 stampata, PDF 17; il testo lo colloca dopo lo sviluppo riuscito del modello.

| Passo del testo | Contenuto effettivo | Applicazione a Roma Bus / artefatto | Stato |
|---|---|---|---|
| 7 | Progettare gli esperimenti, tenendo conto delle combinazioni di parametri e livelli | `configs/experiments.yaml`: confronti pertinenti agli obiettivi. Disegno preliminare ora, riesame prima della produzione dopo verifica, validazione e transitorio | Fase 1 preliminare; consolidamento prima di Fase 5 |
| 8 | Eseguire sistematicamente run di produzione, registrando condizioni iniziali, input e output statistici associati | Manifest di replica con configurazione, dati/versioni, RNG/seed, condizioni iniziali e risultati | Fase 5, nessuna run di produzione eseguita |
| 9 | Analizzare statisticamente l'output del modello stocastico | Metodi documentati su repliche e incertezza in `statistical_protocol.md`; Kurkowski integra le cautele su correlazione, inizializzazione e IC | Protocollo preliminare consolidato; analisi in Fase 5 ancora da eseguire |
| 10 | Usare i risultati per decisioni e valutare le previsioni rispetto alle azioni, quando attuate | Concludere su condizioni critiche, effetti della domanda e regolarità nei limiti del modello; non confondere raccomandazioni con interventi eseguiti | Fase 5 e possibile Fase 6 facoltativa |
| 11 | Documentare risultati, osservazioni, congetture e anche eventuali insuccessi | Relazione, grafici e tabelle, configurazioni riproducibili e limiti di identificabilità | Fasi 5 e 7 |

Il piano accademico locale chiede esperimenti preliminari in Fase 1. Questo non
significa eseguire produzione prima di avere il modello verificato e validato:
si pianifica ora, si riesamina il disegno prima delle run del passo 8.
Il transitorio è un obbligo aggiuntivo esplicito della consegna ed è sostenuto
dalle indicazioni di Kurkowski III.A.1/III.B.2; non viene inventato come dodicesimo
passo numerato dell'algoritmo del libro.

## Cosa queste procedure non prescrivono

Non fissano un algoritmo di selezione delle linee, un PRNG concreto, le
distribuzioni dei tempi bus, i livelli della domanda, il numero di repliche,
una formula di IC o il suo livello. Questi dettagli richiedono lettura mirata
di altre sezioni/fonti e giustificazione per il caso concreto.

Il successivo Algorithm 1.2.1 (p. 16 stampata, PDF 26), incontrato nella ricerca,
è una procedura di calcolo dei ritardi per una coda FIFO a singolo server,
capacità infinita e server inizialmente libero. Non è la seconda procedura
metodologica e non descrive direttamente autobus mobili con servizio batch.
Non sostituire il modello bus con quella ricorrenza per somiglianza del numero.

## Stato e prossimo lavoro

Lettura e mappatura delle procedure metodologiche nel testo fornito completate.
Resta tracciata la differenza di revisione/numerazione rispetto alla bibliografia
ufficiale; prima di citarle come algoritmi dell'edizione 2006 verificarne la
corrispondenza sull'edizione stessa. Non serve inventare nuovi passi per procedere
con il piano documentato sul testo disponibile.

Le fasi di costruzione, verifica, validazione e sperimentazione restano aperte:
leggere le procedure non equivale a eseguirle. Aggiornamento: obiettivi, disegno e
protocollo della Fase 1 consolidati; ulteriori passaggi 3.2 e 8.1/8.3 consultati
e tracciati in `statistical_protocol.md`. In Fase 2 sviluppare separatamente modello
concettuale e specifica degli input.

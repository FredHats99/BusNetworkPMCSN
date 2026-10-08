# Requisiti ufficiali PMCSN AA 2025/2026

Fonte letta integralmente e verificata visivamente: `C:/Users/feder/Desktop/progetto2526.pdf`, due pagine, Prof. V. de Nitto Personè. Le pagine citate sotto sono quelle del PDF. Questa matrice traduce il documento in attività di progetto; gli adempimenti di comunicazione e consegna non sono azioni già eseguite.

**Modalità confermata dall'utente: individuale. Linguaggio C scelto dall'utente.** Il PDF non prescrive uno specifico linguaggio, una rete bus, un numero di linee, una durata di acquisizione o un numero minimo di scenari.

SHA-256 della fonte verificata: `B3490DA5003771F65EEE4B9A39D3ED5EDF406B9EE1A8137A1B25535DD8DC4C85`. Data di lettura: 2026-10-08. La revisione riguarda documentazione e checklist; non modifica il PDF originale né completa le attività di simulazione.

| ID | Requisito | Fonte | Applicabilità e checklist |
|---|---|---|---|
| R01 | Individuare il sistema oggetto dello studio | p. 1, punto 1 | Obbligatorio; 1.3, 2.1 |
| R02 | Individuare obiettivi, motivazioni e miglioramenti attesi | p. 1, punto 2; pp. 1–2, relazione | Obbligatorio; 1.4, 1.8, 5.5, 7.1 |
| R03 | Progettare esperimenti pertinenti al caso e agli obiettivi | p. 1, punto 3 | Obbligatorio; 1.5–1.7, 5.1–5.3 |
| R04 | Costruire il modello seguendo gli algoritmi 1.1 e 1.2 del testo Leemis–Park | p. 1, punto 4 e nota 1 | Obbligatorio; 1.2, 2.1, 3.1. Contenuto degli algoritmi ancora da consultare |
| R05 | Usare le linee guida Kurkowski–Camp–Colagrosso, con particolare attenzione alla sezione III | p. 1, dopo punto 6 e nota 2 | Obbligatorio; 1.2, 1.7. Articolo ancora da consultare |
| R06 | Analizzare comportamento iniziale nel tempo, eventuale convergenza e quando si raggiunge | p. 1, punto 5 | Obbligatorio anche per individuali; Fase 4 |
| R07 | Mostrare transitorio ed esperimenti sia con grafici sia con tabelle numeriche riassuntive | p. 1, punto 6 | Obbligatorio; 4.6, 5.4, 7.3 |
| R08 | Individuale oppure gruppo di massimo 3; per gruppi comunicazione al docente e tutti i partecipanti inclusi nelle email | p. 1, partecipanti | Modalità individuale confermata; 1.1. Adempimenti di gruppo non applicabili |
| R09 | In gruppo includere un algoritmo migliorativo che evolva il modello e ripetere i passi dello studio | p. 1, partecipanti | Non obbligatorio nell'individuale; Fase 6 facoltativa. Se eseguita, resta uno studio rigoroso del sistema modificato |
| R10 | Relazione cartacea: introduzione, sistema, obiettivi, modelli, verifica, validazione, risultati | pp. 1–2, elaborati | Obbligatorio; 3.5–3.6, 7.1 |
| R11 | Descrivere le scelte essenziali e critiche di implementazione | p. 2, elaborati | Obbligatorio; 3.1, 7.2 |
| R12 | Consegnare codice sviluppato senza librerie di sistema, via email o link | p. 2, elaborati | Obbligatorio preparare il pacchetto; 7.4–7.5. Consegna effettiva da registrare separatamente |
| R13 | Nella presentazione includere sistema, obiettivi e orizzonte dello studio motivato | p. 2, presentazione | Obbligatorio; 1.5, 4.5, 7.6 |
| R14 | Individuale: massimo 20 min; gruppo: massimo 10 min per componente | p. 2, presentazione | Limite applicabile: 20 min; 7.7 |
| R15 | Il docente può chiedere esecuzioni durante la presentazione | p. 2, ultima frase | Preparazione necessaria; 7.8. Non significa pubblicare/deployare un servizio web |
| R16 | Valutazione: pertinenza, capacità modellistica/analisi, chiarezza/sintesi, completezza | p. 1, griglia | Checklist di qualità; 1.8, 5.5, 7.9 |

## Distinzione tra requisiti e scelte locali

- **Obblighi:** studio completo, riferimenti metodologici, verifica/validazione, transitorio, risultati grafici e numerici, relazione cartacea, codice e presentazione entro il limite.
- **Scelte del progetto:** Roma Bus, C17, DES, code a capacità finita, GTFS e indicatori scelti. Devono essere pertinenti e motivati, ma non sono prescrizioni specifiche del PDF.
- **Estensioni opzionali:** raccolta realtime prolungata, 3–5 linee, holding/controllo degli headway e ottimizzazione. Nell'individuale non sostituiscono né devono ritardare gli obblighi fondamentali.
- **Modalità temporale:** il PDF chiede di studiare la convergenza, non autorizza a presupporla. Una giornata non stazionaria o uno scenario sovraccarico richiedono diagnosi esplicita e orizzonte motivato.
- **Riferimenti da leggere:** il PDF cita gli algoritmi e l'articolo ma non ne contiene il testo. La casella 1.2 resta aperta; non è stata dedotta una sequenza di passi attribuita arbitrariamente al libro.

## Bibliografia prescritta e suggerita nel PDF

1. L. M. Leemis, S. K. Park, *Discrete-Event Simulation — A First Course*, Pearson Education Prentice Hall, 2006: algoritmi 1.1 e 1.2 richiesti.
2. S. Kurkowski, T. Camp, M. Colagrosso, *MANET Simulation Studies: The Incredibles*, Mobile Computing and Communications Review, 9(4), ottobre 2005: linee guida, in particolare sezione III.
3. M. Harchol-Balter, *Performance Modeling and Design of Computer Systems*, Cambridge University Press, 2013: fonte suggerita per casi di studio.
4. G. Serazzi, *Performance Engineering*, Springer Open Access: capitolo 6 suggerito per casi di studio.

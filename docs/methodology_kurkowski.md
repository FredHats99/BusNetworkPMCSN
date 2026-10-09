# Indicazioni metodologiche da Kurkowski–Camp–Colagrosso

Lettura: 2026-10-09. Fonte fornita dall'utente:
`C:/Users/feder/Desktop/p50-kurkowski.pdf`.
SHA-256: `8545B9383ACA70BB92AF95D4E8093AEDA475396E960650B9E99D58C3EC925B9E`.

S. Kurkowski, T. Camp, M. Colagrosso, *MANET Simulation Studies: The Incredibles*,
Mobile Computing and Communications Review, 9(4), 2005, pp. 50–61, 12 pagine PDF.
Consultata integralmente la sezione III: pp. 53–59 della rivista, pagine PDF 4–10.
Consultate anche introduzione e bibliografia; controllate visivamente le pagine
PDF 4, 7 e 9 per verificare intestazioni, ordine delle colonne e riferimenti.
Le indicazioni sotto sono parafrasi, non citazioni letterali.

## Portata della fonte

L'articolo esamina studi MANET e problemi di credibilità della simulazione:
ripetibilità, assenza di bias, rigore degli scenari e solidità statistica
(sezione I, pp. 50–51). Trasferiamo al caso bus i principi generali, non i
parametri radio, le formule di copertura o le particolarità del vecchio NS-2.
Gli esempi sui PRNG descrivono strumenti e versioni dell'epoca: non sono prove
che un generatore diverso sia adeguato al nostro simulatore.

La sezione I.B (p. 51) rinvia esplicitamente i dettagli del disegno degli
esperimenti alla letteratura DOE. Il testo non contiene un algoritmo per scegliere
linee bus, né sostituisce gli algoritmi Leemis–Park richiesti dal progetto.

## Corrispondenza tra indicazioni effettive e artefatti

| Riferimento | Indicazione effettiva dell'articolo | Applicazione proposta a Roma Bus | Artefatto / fase |
|---|---|---|---|
| III.A.1, p. 53, PDF 4 | Dichiarare se lo studio è terminating o steady-state; non attribuire a una corsa finita proprietà di regime senza accertare la convergenza | Studio finito della finestra 07:00–11:00; conclusioni limitate a quella finestra e agli scenari. Analizzare comunque il transitorio richiesto dal docente | `study_plan.md`, Fasi 1 e 4 |
| III.A.2, p. 53, PDF 4 | Validare il modello base prima degli esperimenti e le modifiche successive; verificare il codice rispetto alle specifiche anche nell'ambiente usato | Separare correttezza dell'implementazione e adeguatezza del modello. Audit GTFS e compilazione non sono validazione del simulatore o della domanda | `model_spec.md`, futuro protocollo di verifica/validazione, Fase 3 |
| III.A.3, pp. 53–54, PDF 4–5 | Accertare che il PRNG sia adatto a dimensioni, quantità di estrazioni e possibili correlazioni dello studio | Scegliere un generatore accademicamente documentato; stimare estrazioni e organizzazione dei flussi prima di usarlo per arrivi, destinazioni e viaggi | Configurazione RNG e documentazione, Fasi 2–3; scelta ancora aperta |
| III.A.4, p. 54, PDF 5 | Impostare esplicitamente le variabili rilevanti senza affidarsi a default che possono cambiare tra versioni | Salvare tutti gli input effettivi: capacità, domanda, OD, travel/dwell, calendari, inizializzazione e arresto; impedire esperimenti con parametri mancanti | `configs/*.yaml`, registro dei parametri, Fase 2 |
| III.A.5, pp. 54–55, PDF 5–6; tabella 3 p. 56 | Caratterizzare gli scenari anche con parametri derivati e studiare dipendenze e topologie; dimensioni nominali non garantiscono una prova rigorosa | Descrivere frequenze/headway per direzione e fermata, sovrapposizioni, domanda e capacità del servizio. Sei linee non dimostrano interazioni se il modello le rende indipendenti | `reports/network_sample.md`, disegno sperimentale e caratterizzazione input, Fasi 1–2 |
| III.B.1, p. 56, PDF 7 | Impostare correttamente i seed; riusare inconsapevolmente lo stesso seed o introdurre correlazioni compromette repliche indipendenti | Registrare seed, stato/stream e associazione a replica; non considerare due esecuzioni identiche come due osservazioni indipendenti | Futuro manifest RNG, Fasi 2–3 e 5 |
| III.B.2, pp. 56–57, PDF 7–8 | Per studi finiti inizializzare in modo pertinente alla finestra; per steady-state affrontare il bias iniziale e giustificare la convergenza. Scartare arbitrariamente un intervallo iniziale non basta | Considerare le 48 corse già in viaggio alle 07:00; distinguere mezzi, carichi e code iniziali. Confrontare inizializzazioni dichiarate; nessun warm-up automatico | `study_plan.md`, configurazione stato iniziale e studio del transitorio, Fasi 2 e 4 |
| III.B.3, p. 57, PDF 8 | Raccogliere output con granularità sufficiente per le metriche e verificare l'analisi già nelle prove preliminari | Tracce di arrivo/boarding del passeggero, identificativi di replica/corsa/linea/direzione/fermata, eventi di negato imbarco e code nel tempo. Verificare che gli output permettano i denominatori e le metriche pianificate | Specifica delle metriche e tracce, Fasi 2–3 |
| III.C.1, p. 58, PDF 9 | Non trattare un'unica esecuzione come verità; motivare il numero di run rispetto alla confidenza richiesta e documentare come è scelto | Pianificare repliche indipendenti; numero determinato con una procedura documentata e precisione concordata, non fissato a 30 perché ritenuto universalmente sufficiente | Protocollo statistico, Fasi 1 e 5 |
| III.C.2, p. 58, PDF 9 | Non applicare formule basate su dati iid senza controllarne le condizioni; cita repliche indipendenti o batch means per affrontare output correlati | Per lo studio finito usare come unità di analisi il risultato della replica; passeggeri e intervalli temporali della stessa corsa simulata non sono repliche indipendenti. Definire e giustificare il metodo concreto prima degli esperimenti | Protocollo statistico, Fasi 1 e 5 |
| III.C.3, p. 58, PDF 9 | Esprimere l'incertezza con intervalli di confidenza, anche nei grafici | Accompagnare confronti e risultati con IC del livello dichiarato; documentare stimatore, unità statistica e ipotesi. Non confondere variabilità simulativa con incertezza dei parametri assunti | Tabelle/grafici risultati, Fasi 4–5 |
| III.D, pp. 58–59, PDF 9–10 | Documentare impostazioni e disponibilità del codice; usare etichette, unità e legende; testo e grafici devono supportarsi chiaramente | Manifest di esecuzione con versione codice, ambiente, input, seed e comandi; grafici con unità, definizioni e discussione. Dichiarare limiti di disponibilità dei dati | Relazione e pacchetto riproducibile, Fasi 5 e 7 |

La colonna di applicazione è una nostra traduzione al caso bus. L'articolo non
prescrive tracce passeggeri, la finestra romana o i nomi dei nostri file.
Le affermazioni sugli scenari di rete provengono dal nostro audit GTFS, non dal PDF.

## Conseguenze concrete per il piano corrente

1. **Tipo temporale:** confermare lo studio finito; nessuna pretesa di regime
   stazionario dalle sole quattro ore simulate. Le condizioni iniziali sono parte
   dello scenario, non un dettaglio da eliminare con un warm-up arbitrario.
2. **Modello base:** inserire un gate di verifica e validazione prima della
   produzione; ripeterlo per modifiche che incidono sul comportamento.
3. **Scenari:** il campione 4+2 è un perimetro locale già autorizzato. Quote e score
   greedy sono scelte esplicite di campionamento, non algoritmi accademici ricavati
   da questo articolo. Conservare la selezione ma valutarne sensibilità e limiti.
   Perturbazioni comuni e indipendenti sono candidati da specificare per studiare
   interazioni, non un disegno già imposto dal testo.
4. **Input:** GTFS non identifica la domanda né dwell realistici. Configurare
   ipotesi esplicite e condizioni fisiche; non etichettarle come dati validati.
5. **RNG:** scegliere e documentare un generatore esistente, la separazione dei
   flussi e i seed. Non inventare un PRNG o dedurre dal testo quale usare in C17.
6. **Output:** definire raccolta e analisi insieme; una simulazione che produce
   soltanto medie globali non basta a verificare attese, censura e transitorio.
7. **Statistica:** le repliche e gli IC sono indicazioni effettive; metodo di IC,
   numerosità, livello e precisione devono ancora ricevere giustificazione propria.

## Scelte che il documento non determina

Non sono prescritti: sei linee, quota 4+2, score di selezione, livelli domanda
0.75/1/1.25, finestra di quattro ore, bin di cinque minuti, 30 repliche pilota,
tetto di 500 repliche, IC al 95%, tolleranza max(5 s, 5%), Student, common random
numbers, thinning o formula per dimensionare la produzione.

I precedenti valori 30/500 e la tolleranza 5 s/5% sono ritirati come valori
operativi. Aggiornamento: protocollo consolidato in `statistical_protocol.md`
dopo consultazione mirata del libro Leemis–Park 3.2 e 8.1/8.3. Scelte locali
40 piloti, 95%, 10 s sono motivate lì e non attribuite a Kurkowski.
Scenari e finestra restano scelte locali distinte dalla fonte.

I batch means non rendono automaticamente iid qualunque serie; servono condizioni
e controlli. L'articolo li cita come approccio, non dà qui una procedura completa
per dimensionare i batch. Analogamente, non basta un periodo PRNG lungo per
dimostrarne l'adeguatezza o seed diversi per assicurare flussi indipendenti.

## Fonti accademiche indicate dall'articolo, ancora da consultare

Riferimenti numerati come nel PDF; reperimento/lettura non ancora dichiarati:

- [4] R. Barton, *Design of experiments: designing simulation experiments*,
  Winter Simulation Conference, 2001, pp. 47–52: disegno degli esperimenti.
- [10] D. Goldsman e G. Tokol, *Output analysis: output analysis procedures for
  computer simulations*, WSC, 2000, pp. 39–45: analisi dell'output.
- [38] S. Sanchez, *Output modeling: abc's of output analysis*, WSC, 2001,
  pp. 30–38: metodi di analisi e inizializzazione.
- [40] L. Schruben, *Detecting initialization bias in simulation output*,
  Operations Research, 1982, pp. 569–590: diagnosi del bias iniziale.
- [2] O. Balci, *Validation, verification, and testing techniques throughout
  the lifecycle of a simulation study*, WSC, 1994, pp. 215–220.
- [39] R. Sargent, *Verification, validation, and accreditation of simulation
  models*, WSC, 2000, pp. 50–59.

Queste fonti integrano, senza sostituire, Leemis–Park. Non attribuiamo loro metodi
specifici prima di consultarne il testo.

## Stato della checklist

Consultazione e corrispondenza della sezione III completate per R05/1.2.
Applicazione nei futuri simulatori e risultati ancora da verificare. Aggiornamento:
consultate anche le procedure del PDF Leemis–Park fornito dall'utente, documentate
in `methodology_leemis_park.md` con nota sulla revisione e numerazione. Il punto 1.2
è concluso per consultazione e mappatura dei testi disponibili.
Nessun esperimento o test statistico è stato eseguito da questa lettura.

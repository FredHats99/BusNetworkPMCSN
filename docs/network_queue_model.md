# Modello completo: code alle fermate e autobus a capacità finita

Aggiornamento 2026-10-22: i punti operativi indicati aperti nella prima
formulazione sono chiusi dal [contratto congelato](phase2_operational_contract.md).
Le identità matematiche restano valide nei rispettivi domini; la Fase 3 deve
ancora implementarle e verificarle.

Formule del riferimento stabile: [occupazione, disponibilità e tempi medi
nel caso non sovraccarico](non_overloaded_route_formulas.md).

Data: 2026-10-16. Stato: prima formulazione matematica, non configurazione
eseguibile. Nessuna simulazione eseguita per questo documento.

## 1. Obiettivo e rapporto con il caso controllato

Nel [caso controllato](controlled_queue_model.md) ogni passaggio offre c posti
fissi. Qui la disponibilità deriva dai passeggeri a bordo e dalle discese.
Le code sono quindi accoppiate lungo il percorso attraverso gli autobus.

L'obiettivo è descrivere la dinamica e ottenere indicatori complessivi della
tratta. Si conservano i valori per fermata nello stato interno, senza imporre
che le loro medie coincidano. Non si assume a priori un regime stazionario
nella finestra finita 07:00–11:00.

## 2. Notazione e stato

| Simbolo | Significato |
|---|---|
| q = (s,l,d) | Coda alla fermata GTFS s, linea l, direzione d |
| lambda_q(t) | Tasso degli arrivi alla coda q, costante in fasce di 30 minuti |
| k | Identificativo della corsa/autobus, non necessariamente indice temporale |
| i | Posizione della fermata nella sequenza della corsa k |
| C_k | Capacità fissa del mezzo assegnato alla corsa k |
| t^a_(k,i), t^p_(k,i) | Istanti di arrivo e partenza dalla fermata |
| N^-_(k,i) | Persone a bordo immediatamente prima delle discese |
| D_(k,i) | Persone che scendono |
| R_(k,i) | Posti liberi dopo le discese, prima delle salite |
| B_(k,i) | Persone che salgono durante la visita |
| N^+_(k,i) | Persone a bordo alla partenza |

C_k non varia durante la corsa: il pedice distingue mezzi con capacità diverse.
Il mix sintetico 50–50 fra standard e articolati non rende casuale la capacità
durante il viaggio. Valori numerici e assegnazione delle classi restano aperti.

Lo stato comprende: code FIFO con istante di arrivo e destinazione di ciascun
passeggero; posizione e stato dei mezzi; passeggeri a bordo con destinazione;
calendario degli eventi e integrali necessari alle statistiche. Il solo numero
totale di passeggeri a bordo non determina le discese successive.

## 3. Arrivi e scelta della destinazione

Per intervalli deterministici [u,v), il numero di nuovi arrivi alla coda q è:

    A_q[u,v) ~ Poisson(integrale(u,v) lambda_q(t) dt).

Per la stessa coda, gli incrementi su intervalli disgiunti sono indipendenti.
L'indipendenza fra code diverse resta un'ipotesi da fissare. Se un intervallo
attraversa più fasce, la media è la somma dei contributi delle singole fasce.
Non assumere automaticamente arrivi Poisson condizionati a intervalli casuali
di passaggio: i tempi dei bus possono dipendere dalla domanda e dalle soste.

Ogni passeggero sceglie all'arrivo una destinazione uniforme nell'insieme
ammissibile a valle per origine, linea e verso. Sale soltanto su una variante
che la raggiunge. La costruzione dell'insieme per varianti, pickup/dropoff e
fermate ripetute deve essere definita negli input. Non generare arrivi senza
destinazioni ammissibili. Nessun trasbordo, abbandono o cambio di linea.

## 4. Bilanci a ogni visita

Le discese precedono le salite:

    D_(k,i) = numero di passeggeri a bordo con destinazione alla visita corrente
    R_(k,i) = C_k - N^-_(k,i) + D_(k,i)
    N^+_(k,i) = N^-_(k,i) - D_(k,i) + B_(k,i).

Vincoli esatti:

    0 <= D_(k,i) <= N^-_(k,i) <= C_k
    0 <= B_(k,i) <= R_(k,i)
    0 <= N^+_(k,i) <= C_k.

In assenza di eventi intermedi di salita/discesa:

    N^-_(k,i+1) = N^+_(k,i).

La disciplina è FIFO fra passeggeri compatibili. Un passeggero incompatibile
non impedisce la salita degli altri. Una corsa incompatibile non costituisce
un imbarco negato per capacità.

Con imbarco istantaneo e Q_amm passeggeri compatibili presenti:

    B_(k,i) = min(Q_amm, R_(k,i)).

Questa ultima formula riguarda il sottocaso istantaneo, non tutta la visita
con sosta non nulla. Nel modello completo già concordato, chi arriva durante
l'imbarco può salire se compatibile e se resta posto. La sosta dipende dal
servizio. L'imbarco termina a bus pieno o coda compatibile vuota; nessuna salita
durante la chiusura. Per una visita servita la sosta è 5 + D_(k,i) + 2 B_(k,i)
secondi. Senza discese e senza persone compatibili all'arrivo la sosta è nulla.
Precedenze simultanee e capolinea restano da specificare. Coefficienti e regole
in [phase2_inputs.md](phase2_inputs.md).

## 5. Bilanci delle code

Per ogni coda q e intervallo [u,v), con convenzioni coerenti sugli estremi:

    Q_q(v) = Q_q(u) + A_q[u,v) - B_q[u,v),

dove B_q conta tutti gli imbarchi effettivi dalla coda, anche se avvenuti durante
le soste. L'assenza di abbandoni rende questo un controllo esatto per replica.

Il residuo a una fermata dipende dal carico proveniente da monte. I posti
disponibili e le code possono essere dipendenti, anche fra passaggi successivi.
Non sostituire quindi il modello completo con code indipendenti a c fisso
senza dichiarare un'approssimazione.

## 6. Discese uniformi: riferimento su un percorso semplice

Solo per un percorso 1,...,m senza varianti o fermate ripetute, con tutte le
destinazioni successive ammissibili, il passeggero salito in a sceglie fra
a+1,...,m. Se è ancora a bordo prima della fermata i:

    P(destinazione = i | destinazione >= i, origine = a) = 1/(m-i+1).

Con scelte indipendenti e ammissione che non seleziona le destinazioni residue,
il corrispondente riferimento aggregato è:

    D_i | N^-_i = n ~ Binomiale(n, 1/(m-i+1)).

La simulazione conta invece le destinazioni già assegnate; non effettua una
seconda estrazione per le discese. Questa binomiale non implica che N^-_i sia
binomiale su C posti. Con varianti, gruppi con destinazioni ammissibili diverse
o condizioni iniziali diverse non applicare automaticamente la stessa legge.

## 7. Tempo a bordo e medie complessive

Il tempo di servizio del passeggero a bordo è S = istante di discesa - istante
di salita, distinto dall'attesa W_q prima della salita e dal tempo di imbarco.

Per un percorso semplice con tempi t_ij fissati e destinazioni uniformi:

    E[S | origine = i] = (1/(m-i)) somma(j=i+1,...,m) t_ij.

Questa formula richiede che i tempi usati rappresentino il viaggio delle
persone effettivamente imbarcate; con tempi dipendenti da carico e destinazioni
occorre mantenere il relativo condizionamento, non sostituire medie arbitrarie.

Nel riferimento omogeneo con tempo tau per ogni tratto, tassi lambda uguali
alle prime m-1 fermate e regime stabile senza abbandoni:

    E[S | origine = i] = tau (m-i+1)/2
    E[S] = tau (m+2)/4
    Lambda = (m-1) lambda.

Un lambda medio non giustifica da solo origini uniformi: tassi uguali sono
un'ipotesi esplicita di questo riferimento.

In un regime stabile compatibile con Little:

    L_bordo = Lambda E[S]
    L_q = Lambda E[W_q]
    L_totale = L_q + L_bordo.

L_bordo è il numero medio contemporaneamente a bordo di tutti i bus; L_q è
la somma delle code medie temporali. E[S] ed E[W_q] sono medie per passeggero.
Queste identità non determinano da sole L_q o E[W_q].

Per il riferimento a bus identici, passaggi h e durata fissa T_r, il numero
medio di bus in tratta è M = T_r/h. Il rapporto fra integrali di occupazione e
presenza dei bus, ossia l'occupazione media per unità di tempo-bus, è:

    N_barra = L_bordo / M.

Con C fisso per tutti i bus, l'utilizzo medio dei posti è N_barra/C. Non è
una condizione sufficiente di stabilità per ogni coda o tratto. Nella flotta
eterogenea distinguere media del rapporto N/C e rapporto degli integrali:
sono indicatori diversi, da denominare e misurare separatamente.

## 8. Misure finite nella finestra dello studio

Per T = 11:00 e t0 = 07:00, registrare almeno:

    coda media temporale = integrale(t0,T) somma_q Q_q(t) dt / (T-t0)

    occupazione media per tempo-bus =
      integrale(t0,T) somma_bus N_bus(t) dt /
      integrale(t0,T) numero_bus_presenti(t) dt.

Specificare quali mezzi e quali porzioni di corsa sono inclusi. Se non vi è
tempo-bus osservato, il secondo rapporto non è definito.

Per la coorte entrata in [t0,T), sommare l'attesa dalla propria entrata fino
alla salita o a T se non ancora salita; la media include tutti gli arrivi,
non soltanto quelli serviti. Separare i passeggeri iniziali. L'integrale delle
sole persone in coda appartenenti alla coorte coincide esattamente con tale
somma di attese limitate: è un controllo per replica. Una coorte vuota segue
le convenzioni del protocollo statistico, non genera un'attesa zero arbitraria.

Non applicare automaticamente Little stazionario alla finestra finita. Code
residue, corse in viaggio e passeggeri ancora a bordo sono risultati da
registrare, non errori da eliminare mediante esclusioni implicite.

## 9. Piano di verifica e limiti dei riferimenti

- Riprodurre il caso controllato con posti fissi, imbarco istantaneo e servizio
  periodico; usare i suoi riferimenti per coda e attesa.
- Verificare separatamente destinazioni, discese e tempi a bordo sul percorso
  semplice, con condizioni coerenti con le formule del riferimento.
- Verificare bilanci di code e bus su ogni replica del modello completo.
- Usare controlli di riduzione: il modello completo deve riprodurre il caso
  controllato quando è configurato con le stesse regole.
- Per la rete completa confrontare indicatori complessivi e risultati per linea
  mantenendo tracce locali utili a diagnosticare errori e tratti critici.

Non si adotta una distribuzione binomiale dell'occupazione del bus né si usa
c_barra al posto di R_(k,i) come se fosse un'identità. La serie di Spitzer del
caso controllato non si trasferisce automaticamente a disponibilità dipendenti
e passaggi irregolari. Eventuali approssimazioni vanno confrontate e denominate.

## 10. Decisioni ancora necessarie

Capacità delle due classi e assegnazione delle corse; tassi assoluti e profili
tra fermate; indipendenza delle code; destinazioni ammissibili nelle varianti;
leggi dei tempi di viaggio e dominio condiviso; regole dei capolinea;
precedenze degli eventi; stato iniziale delle corse già in viaggio e delle
code; arresto ed eventuale drenaggio. La Fase 2 rimane aperta.

Riferimenti del progetto: [modello concettuale](model_spec.md),
[caso controllato](controlled_queue_model.md),
[protocollo statistico](statistical_protocol.md).

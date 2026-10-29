"""Export the complete assertion table and an Italian gate report from retained results."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
STATUS = {"passed": "superato", "failed": "non superato", "inconclusive": "inconcludente", "accepted": "accettato"}


def render(directory, verbose=True):
    summary = json.loads((directory / "gate38_results.json").read_text())
    manifest = json.loads((directory / "manifest.json").read_text())
    criteria = json.loads((directory / "criteria.json").read_text())
    criteria_source = manifest.get("criteria_source", "configs/gate38_criteria.json").replace("\\", "/")
    protocol_source = criteria.get("protocol", "docs/gate38_protocol.md")
    assertions = json.loads((directory / "assertions.json").read_text())
    diagnostics = json.loads((directory / "diagnostics.json").read_text())
    sidecar = json.loads(Path(manifest["cases"][0]["manifest"]).read_text())
    stop_ids = sidecar["stop_index"]
    csv_path = ROOT / "reports/gate38_assertions.csv"
    fields = ["kind", "case", "other", "group", "route_id", "direction_id", "from_stop_id", "to_stop_id", "metric",
              "status", "reason", "available_replicas", "required_replicas", "target", "margin", "mean", "deviation",
              "interval_low", "interval_high", "standard_error", "critical_value", "replica_min", "replica_max"]

    def arc_labels(group):
        if not group.startswith("arc|"):
            return {}
        _, route, direction, start, end = group.split("|")
        return dict(route_id=route, direction_id=direction, from_stop_id=stop_ids[int(start)], to_stop_id=stop_ids[int(end)])

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fields, extrasaction="ignore")
        writer.writeheader()
        for row in assertions:
            low, high = row.get("interval_deviation", [None, None])
            writer.writerow({**row, **arc_labels(row["group"]), "interval_low": low, "interval_high": high})
    counts = summary["assertion_counts"]
    broad = [a for a in assertions if not a["group"].startswith("arc|")]
    arc = [a for a in assertions if a["group"].startswith("arc|")]
    coverage = Counter(a["reason"] for a in assertions if a["status"] == "inconclusive")
    selected_stats = {}
    with (directory / "replica_statistics.jsonl").open() as f:
        for line in f:
            row = json.loads(line)
            selected_stats.setdefault((row["case"], "network"), []).append(row["groups"]["network"])

    def observed(case, group, key):
        values = [r[key] for r in selected_stats.get((case, group), []) if r.get(key) is not None]
        return statistics.fmean(values) if values else None

    def fnum(value):
        return "NA" if value is None else f"{value:.5g}"

    lines = ["# Gate 3.8 — diagnostica e criteri di accettazione", "",
             f"Esito della versione {criteria['criteria_version']}: **{STATUS[summary['status']]}**.", "",
             f"Eseguite {summary['replicas']} repliche: {criteria['replicas_per_case']} per ognuno dei sei scenari e dei due stati iniziali. "
             "Non sono il pilota o la produzione. Gli stream sono continuati anche fra scenari, dopo il prefisso disgiunto delle prove precedenti.", "",
             "Requisiti esatti e prerequisiti software: **superati**. Ogni ingresso nel tratto, anche con arrivo dopo le 11, "
             "è stato verificato contro gli input, le chiavi ambientali, i riusi, i consumi RNG e lo stato finale dei bus.", "",
             f"Inventario fissato prima delle run: {len(manifest['arc_groups'])} archi nominali, "
             f"{len(manifest['broad_groups'])} gruppi aggregati, {summary['family_size']} asserti. "
             "IC Student bilaterali con Bonferroni, confidenza simultanea nominale 95%; copertura approssimata per output non normali.", "",
             "## Esiti obbligatori", "", "| Famiglia | Superati | Non superati | Inconcludenti |", "|---|---:|---:|---:|"]
    for family, count in summary["by_kind"].items():
        lines.append(f"| {family} | {count.get('passed', 0)} | {count.get('failed', 0)} | {count.get('inconclusive', 0)} |")
    lines.extend(["", f"Totale: {counts.get('passed', 0)} superati, {counts.get('failed', 0)} non superati, "
                  f"{counts.get('inconclusive', 0)} inconcludenti.", "",
                  "Un IC interamente entro il margine accetta l'equivalenza operativa; interamente fuori la respinge; "
                  "un IC a cavallo del limite lascia il controllo inconcludente. Nessun margine o numero di repliche è stato adattato agli esiti.", "",
                  f"Inconcludenti per precisione: {coverage.get('insufficient_precision', 0)}; "
                  f"per copertura incompleta: {coverage.get('insufficient_coverage', 0)}.", "",
                  "## Marginali aggregate: rete, linea/direzione e dominio", "",
                  "I fattori sono valutati contro media 1, CV 0.2 e CDF ai quantili 0.10/0.25/0.50/0.75/0.90. "
                  "Per SHARED–BASE e SHARED_D125–D125 si confrontano anche le differenze delle stesse statistiche. "
                  "Le tolleranze locali sono ±0.02, ±0.03 e ±0.03 rispettivamente. REGULAR è controllato esattamente e non confrontato sul CV.", "",
                  "| Caso | Media fattore rete | CV rete | Controlli aggregati superati / totali |", "|---|---:|---:|---:|"])
    for case in manifest["cases"]:
        relevant = [a for a in broad if a["case"] == case["id"] and a["kind"] == "reference_marginal"]
        lines.append(f"| {case['id'].replace('|', ' / ')} | {fnum(observed(case['id'], 'network', 'mean'))} | "
                     f"{fnum(observed(case['id'], 'network', 'cv'))} | {sum(a['status'] == 'passed' for a in relevant)} / {len(relevant)} |")
    lines.extend(["", "## Archi e tempi medi", "",
                  "Sono obbligatori lo scostamento medio dal riferimento e i confronti BASE–REGULAR, SHARED–BASE, "
                  "SHARED_D125–D125 sui tempi medi effettivi, con margine ±10 secondi. L'insieme degli archi viene dal calendario, "
                  "non viene ridotto in base ai passaggi osservati. Un arco assente in una replica non viene imputato a zero.", "",
                  "La media effettiva è scomposta in media del riferimento selezionato più scostamento medio dovuto al fattore. "
                  "Cambiamenti nei bus che raggiungono un arco entro T possono cambiare anche la composizione dei riferimenti.", "",
                  "| Confronto | Stato iniziale | Superati | Non superati | Inconcludenti |", "|---|---|---:|---:|---:|"])
    for mode in criteria["initializations"]:
        for a, b in criteria["comparisons"]:
            subset = [x for x in arc if x["kind"] == "comparison_arc_time" and x["case"] == f"{a}|{mode}" and x["other"] == f"{b}|{mode}"]
            c = Counter(x["status"] for x in subset)
            lines.append(f"| {a}–{b} | {mode} | {c['passed']} | {c['failed']} | {c['inconclusive']} |")
    blockers = sorted([a for a in assertions if a["status"] != "passed"],
                      key=lambda a: (a["status"] == "failed", abs(a.get("deviation", 0))/a["margin"]), reverse=True)
    if blockers:
        lines.extend(["", "## Esempi dei controlli che impediscono l'accettazione", "",
                      "La tabella seguente mostra fino a 15 casi; il CSV conserva l'intero inventario, compresi gli esiti favorevoli.", "",
                      "| Caso/confronto | Gruppo | Metrica | Deviazione | IC deviazione | Margine | Esito |", "|---|---|---|---:|---|---:|---|"])
    else:
        lines.extend(["", "## Esiti bloccanti", "", "Nessuno: tutti gli asserti obbligatori sono superati."])
    for a in blockers[:15]:
        labels = arc_labels(a["group"])
        group = f"{labels['route_id']} dir {labels['direction_id']}: {labels['from_stop_id']}→{labels['to_stop_id']}" if labels else a["group"].replace("|", " / ")
        case = a["case"].replace("|", " / ") + (" − " + a["other"].split("|")[0] if "other" in a else "")
        ci = ", ".join(fnum(v) for v in a.get("interval_deviation", [None, None]))
        lines.append(f"| {case} | {group} | {a['metric']} | {fnum(a.get('deviation'))} | [{ci}] | {a['margin']} | {STATUS[a['status']]} |")
    lines.extend(["", "## Diagnostiche supplementari", "",
                  "Nei dati completi sono conservate per replica anche CDF/CV di ogni arco, distribuzione delle sole chiavi nuove, "
                  "riusi, composizione dei riferimenti e strati per bin ambientale. La verifica inferenziale obbligatoria "
                  "delle marginali riguarda i gruppi aggregati; a livello di singolo arco è obbligatoria la verifica delle medie in secondi. "
                  "Non si dichiara equivalenza dell'intera distribuzione su ogni arco.", "",
                  f"Totale ingressi nei tratti: {sum(d['traversals'] for d in diagnostics)}; "
                  f"ingressi con arrivo alle 11 o dopo: {sum(d['unfinished_traversals'] for d in diagnostics)}. "
                  "Questi ultimi sono inclusi nelle statistiche dei tempi assegnati.", "",
                  "## Decisione e attività successive", ""])
    if summary["status"] == "accepted":
        lines.append("Accettato soltanto entro il perimetro e le tolleranze dichiarate. Prima della produzione restano transitorio, "
                     "riesame dei confini e orchestrazione della campagna statistica.")
    else:
        lines.append("Il gate 3.8 resta aperto. La diagnostica è completa per questo protocollo, ma i requisiti di equivalenza non sono tutti soddisfatti.")
        if coverage.get("insufficient_coverage"):
            lines.append("Gli asserti senza copertura richiedono un disegno che dia osservazioni agli archi rari o una revisione esplicita del perimetro.")
        else:
            lines.append("Tutti i gruppi obbligatori hanno copertura completa. Gli esiti inconcludenti dipendono dalla precisione: "
                         f"{criteria['replicas_per_case']} repliche non bastano per alcuni margini con questa correzione simultanea. Occorre pianificare e congelare "
                         "una nuova campagna indipendente prima di raccogliere altri dati; nessun aumento automatico delle repliche.")
        if counts.get("failed"):
            lines.append("Gli IC interamente fuori margine richiedono inoltre di verificare selezione endogena e composizione dei riferimenti "
                         "prima di correggere il modello o limitare l'interpretazione dei confronti.")
        else:
            lines.append("Nessun IC obbligatorio è interamente fuori margine: non emerge una violazione conclusiva dei margini, "
                         "ma questo non dimostra equivalenza. Le medie puntuali oltre soglia con IC ampio non sono da sole prova di un bug.")
    if "confirmation" in summary and criteria.get("planning_campaign"):
        confirm = summary["confirmation"]
        lines.extend(["", "## Separazione dalla pianificazione", "",
                      "Questa decisione usa soltanto il campione nuovo. Le 384 repliche v1 sono usate per diagnosi e dimensionamento, non per gli IC finali.",
                      f"Obiettivi di semiampiezza entro metà margine: {confirm['precision_targets_met']} / {confirm['precision_targets_total']}.",
                      "Nessuna estensione automatica della campagna in base all'esito."])
        prior_path = ROOT / criteria["planning_campaign"] / "assertions.json"
        prior_assertions = json.loads(prior_path.read_text())
        identity = lambda a: (a["kind"], a["case"], a.get("other"), a["group"], a["metric"])
        lookup = {identity(a): a for a in assertions}
        prior_blockers = [a for a in prior_assertions if a["status"] != "passed"]
        resolved = sum(lookup[identity(a)]["status"] == "passed" for a in prior_blockers)
        lines.extend(["", f"Controlli precedentemente inconcludenti ora superati: {resolved} / {len(prior_blockers)}."])
        previous_worst = max(prior_blockers, key=lambda a: abs(a.get("deviation", 0))/a["margin"])
        new_worst = lookup[identity(previous_worst)]
        labels = arc_labels(previous_worst["group"])
        if labels:
            new_ci = new_worst["interval_deviation"]
            lines.extend([f"Il caso precedentemente più vicino/oltre soglia, linea {labels['route_id']} direzione {labels['direction_id']} "
                          f"{labels['from_stop_id']}→{labels['to_stop_id']}, passa da una stima diagnostica {previous_worst['deviation']:.5f} s "
                          f"a {new_worst['deviation']:.5f} s nel campione indipendente, con IC simultaneo "
                          f"[{new_ci[0]:.5f}, {new_ci[1]:.5f}] s, interno al margine ±{new_worst['margin']:g} s.",
                          "Le stime provengono da campioni separati; i dati di pianificazione non sono stati accodati agli intervalli finali."])
    reproduction = f"python scripts/gate38.py --criteria {criteria_source} --exe {Path(manifest['executable']).relative_to(ROOT).as_posix()} --output-dir data/processed/phase3/REPRODUCTION_NEW_DIRECTORY"
    lines.extend(["", "La domanda, l'OD e i tempi restano sintetici: questa diagnostica non è validazione empirica del servizio reale.", "",
                  "## Riproduzione e audit", "", "```powershell", reproduction,
                  f"python scripts/gate38.py --analyze-only {directory.relative_to(ROOT).as_posix() if directory.is_relative_to(ROOT) else directory}",
                  f"python scripts/render_gate38_report.py {directory.relative_to(ROOT).as_posix() if directory.is_relative_to(ROOT) else directory}", "```", "",
                  "Una riproduzione richiede una directory nuova (`--output-dir`); il runner non sovrascrive campagne precedenti. "
                  "Cambiare soltanto directory ripete le stesse sequenze e non aggiunge repliche indipendenti. Una campagna successiva "
                  "richiede un protocollo versionato e un tratto RNG disgiunto o una continuazione verificata degli stati.",
                  f"Criteri: `{criteria_source}`; protocollo: `{protocol_source}`; "
                  "esito strutturato: `reports/gate38_results.json`; tutti gli asserti: `reports/gate38_assertions.csv`.", "",
                  f"SHA256 criteri: `{summary['criteria_sha256']}`. SHA256 inventario: `{summary['inventory_sha256']}`."])
    if "rng_version" in summary:
        lines.extend(["", "## Generatore e budget", "", f"Generatore: `{summary['rng_version']}`.",
                      "Blocchi Lehmer disgiunti; stati iniziali/finali verificati con esponenziazione modulare Python.",
                      "Nessun campione MRG32k3a incluso nella decisione.",
                      f"Obiettivi di semiampiezza: {summary['confirmation']['precision_targets_met']} / {summary['family_size']}."])
    (ROOT / "reports/gate38_results.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    renderer = dict(renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    assertions_csv_sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                    report_sha256=hashlib.sha256((ROOT / "reports/gate38_results.md").read_bytes()).hexdigest())
    (ROOT / "reports/gate38_report_manifest.json").write_text(json.dumps(renderer, indent=2)+"\n")
    if verbose:
        print(json.dumps(dict(status=summary["status"], broad_assertions=dict(Counter(a["status"] for a in broad)),
                              arc_assertions=dict(Counter(a["status"] for a in arc)), inconclusive_reasons=dict(coverage)), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    render(parser.parse_args().directory.resolve())

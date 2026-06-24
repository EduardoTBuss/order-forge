# E-Mail-Verlauf — Änderungsmitteilung Bauprofil

---

## Nachricht 1 — Bauprofil an AluProfil

**Von:** Matthias König <m.koenig@bauprofil-elemente.de>
**An:** Sabine Vogt <s.vogt@aluprofil.de>
**Datum:** 22.06.2026, 09:14
**Betreff:** AW: Bestellung BP-2026-00487 — Änderung Pos. 030

---

Hallo Frau Vogt,

bezugnehmend auf unsere Bestellung BP-2026-00487 vom 15.06. (Bürokomplex
Stuttgart-Ost, Fassadenelemente Phase 2) müssen wir leider folgende Änderung
melden:

**Pos. 030 — Solar-Montageschiene AE-2025-020:**
- Ursprünglich: 2.400 kg, Liefertermin 01.10.2026
- **Neu:** 2.800 kg, Liefertermin unverändert 01.10.2026

Grund: Der Statiker hat den Windlastnachweis für die Dachfläche verschärft.
Wir brauchen 12 zusätzliche Schienenstränge à 33 m. Entspricht bei
1,28 kg/m etwa +400 kg.

Die übrigen Positionen bleiben unverändert.

Bitte senden Sie uns eine aktualisierte Auftragsbestätigung. Entschuldigen
Sie die kurzfristige Änderung — das Planungsbüro hat den Nachweis erst
gestern Abend freigegeben.

Mit freundlichen Grüßen,
Matthias König
Leiter Einkauf / Bauprofil Bauelemente GmbH

---

## Nachricht 2 — Sabine an Team (intern weitergeleitet)

**Von:** Sabine Vogt <s.vogt@aluprofil.de>
**An:** Frau Demir <a.demir@aluprofil.de>, Marco Berger <m.berger@aluprofil.de>
**Datum:** 22.06.2026, 09:22
**Betreff:** WG: Bauprofil BP-2026-00487 — Änderung Pos. 030

---

Demir,

bitte in MetallSoft die Pos. 030 von 2.400 auf 2.800 kg ändern. Restliche
Positionen unverändert. Auftragsbestätigung neu auslösen.

Marco: Das ist genau der Fall, den ich gestern meinte. Solche Änderungen
kommen praktisch täglich. Im aktuellen Prozess muss Frau Demir die
Bestellung manuell suchen, die Position ändern, neu speichern, AB neu
drucken. Wenn das alles automatisch läuft — wie kriegt das System die
Änderungsmitteilung mit? Aus einer E-Mail? Aus einer zweiten PDF?

Das müssen wir mit Machines Like Me besprechen. Die Lösung muss mit
Änderungen umgehen können, nicht nur mit Erstbestellungen.

Gruß,
Sabine

---

## Nachricht 3 — Marco an Sabine und Clara

**Von:** Marco Berger <m.berger@aluprofil.de>
**An:** Sabine Vogt <s.vogt@aluprofil.de>, Clara Mendes <c.mendes@machineslikeme.com>
**Datum:** 22.06.2026, 10:01
**Betreff:** Re: WG: Bauprofil BP-2026-00487 — Änderung Pos. 030

---

Clara,

anbei ein Live-Beispiel, warum reine PDF-Extraktion nicht reicht. Wir
bekommen nachträgliche Änderungen — per E-Mail, manchmal per Anruf, selten
als formelles Änderungs-PDF. Das Intake-System muss:

1. Die ursprüngliche Bestellung erkennen (Referenznummer BP-2026-00487)
2. Die geänderten Positionen identifizieren (nur Pos. 030)
3. Den Rest der Bestellung unangetastet lassen
4. Im Idealfall eine regelbasierte Plausibilitätsprüfung machen (+400 kg
   bei 1,28 kg/m ≈ 312 m ≈ 10 zusätzliche Schienen — klingt plausibel)

Können wir das im Prototypen abbilden? Das wäre ein starkes Argument in der
nächsten Präsentation.

Gruß,
Marco

---

## Notiz von Clara (intern, Machines Like Me)

**Datum:** 22.06.2026, 10:30

Wichtiger Punkt für den Prototypen: Änderungsmanagement. Mindestens
folgende Fälle unterscheiden:
- Mengenänderung (häufigster Fall — siehe oben)
- Stornierung einer Position
- Neue Position hinzugefügt
- Lieferterminverschiebung
- Komplettstornierung des Auftrags

Technisch: Referenznummer-Matching auf bestehende Aufträge. Bei Treffer:
Änderung statt Neuanlage. Dieses Feature für V2 vormerken, für den ersten
Prototyp reicht die Erkennung und Markierung "Mögliche Änderung zu
bestehendem Auftrag BP-2026-00487".

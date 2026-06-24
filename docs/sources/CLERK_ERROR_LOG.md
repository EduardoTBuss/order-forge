# Clerk Error Log — Manuelle Auftragserfassung (Auszug)

**Quelle:** AluProfil Systemtechnik GmbH, Team Sabine Vogt
**Datum:** KW 24/2026 (ausgefüllt von Frau Demir, Sachbearbeiterin)
**Vermerk:** Fehler, die während der manuellen Erfassung in MetallSoft
aufgefallen und korrigiert wurden. Nur dokumentierte Fälle.

---

| # | Datum | Kunde | Fehlertyp | Original (PDF) | Was erfasst worden wäre | Korrektur | Grund |
|---|-------|-------|-----------|----------------|------------------------|-----------|-------|
| 1 | 09.06 | Bauprofil DE | **Einheit** | 150 Stk. Winkel 40×40×3 | 150 Stk. → als 150 m interpretiert | 150 Stk. = 150 × 6 m = 900 m Gesamtlänge | Positionsmenge war "150" ohne klare Einheit; erst der Blick in die Artikeltabelle zeigte Stück. |
| 2 | 10.06 | FensterSystem CH | **Legierung** | PR-WIN-6060-FR-01 (Fensterrahmen) | EN AW-6060 T5 | EN AW-6060 T66 | Kunde schreibt nie das Temper; es steht in unserer internen Spezifikation. T5 ist für Fensterprofile zu weich. |
| 3 | 10.06 | ConstruxAlu FR | **Code** | "ALU 6060, cornière 30×30" | Neuer Artikel anlegen | AE-2024-033 existiert bereits | "ALU 6060" ist ConstruxAlus Schreibweise für EN AW-6060. Wir haben das Profil schon im Katalog. |
| 4 | 11.06 | Nordic Profiles | **Fehlende Art.-Nr.** | "40×40×3, 6060, 6000 mm" | Kein Code → manuelle Suche im Katalog | AE-2024-034 | Nordic gibt nie unsere Codes an. Wir suchen nach Abmessungen und Legierung. Dauert pro Position ~3 min. |
| 5 | 11.06 | ConstruxAlu FR | **TBD-Position** | "À DÉFINIR — cornière fixation" | — (nicht erfasst) | Rücksprache mit Sabine: Kunde anrufen, Spezifikation anfordern | Ohne Spezifikation kann nichts bestellt werden. Position bleibt offen. |
| 6 | 12.06 | FensterSystem CH | **Währung** | CHF 14.500,00 | EUR 14.500,00 (falsch) | CHF → EUR umrechnen (× 1,02) | FensterSystem bestellt in CHF. MetallSoft arbeitet in EUR. Umrechnung muss manuell erfolgen. |
| 7 | 12.06 | Bauprofil DE | **Liefertermin** | 15.09.2026 (in Tabelle) / 01.09.2026 (im Text) | 15.09.2026 | Nachfrage bei Sabine: 01.09. ist der korrekte Wunschtermin des Kunden. | Zwei widersprüchliche Daten im selben PDF. Kommt häufiger vor, als man denkt. |
| 8 | 13.06 | ConstruxAlu FR | **Mengeneinheit** | 1.500 kg (Solar-Schiene) | 1.500 Stk. | 1.500 kg, Umrechnung: ca. 1.170 m oder ca. 195 Stk. à 6 m | Verwechslung kg ↔ Stk. passiert regelmäßig, besonders bei französischen und schwedischen Aufträgen. |
| 9 | 13.06 | Nordic Profiles | **Alloy-Synonym** | "AlMg0.7Si" | "Unbekannte Legierung" → Rückfrage | EN AW-6063 | Unsere älteren Kollegen kennen die DIN-Bezeichnungen. Neue Mitarbeiter kennen nur EN AW-Codes. |
| 10 | 14.06 | FensterSystem CH | **Kalenderwoche** | "KW 38/2026" | Als Datum falsch interpretiert (38. Monat existiert nicht) | 15.09.–21.09.2026 | MetallSoft akzeptiert nur konkrete Daten, keine KW-Angaben. Umrechnung manuell. |

---

**Zusammenfassung der Woche (Demir):**
- 10 dokumentierte Fehler bei ~45 manuell erfassten Aufträgen
- Häufigste Fehlerquellen: Legierungs-Synonyme (3×), Mengeneinheiten (2×), fehlende Artikelnummern (2×)
- Zeitaufwand für Fehlerkorrektur: ca. 1,5 h / Woche
- 3× Rücksprache mit Sabine nötig (Kundenkontakt)
- 1 offener Posten (ConstruxAlu TBD) — wartet auf Kundenspezifikation

*"Wenn die KI wenigstens die Einheiten und Legierungen automatisch erkennen könnte, würde das schon die Hälfte der Fehler vermeiden." — Frau Demir, 14.06.2026*

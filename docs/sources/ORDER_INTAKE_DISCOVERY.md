# Order Intake — First Discovery Meeting

**Date:** 2026-06-10, 09:00–10:30
**Location:** AluProfil Systemtechnik GmbH, Industriestraße 42, D-40589 Düsseldorf — Besprechungsraum "Alu"
**Attendees:**
- Marco Berger, Operations Director, AluProfil
- Sabine Vogt, Head of Sales, AluProfil
- Thomas Keller, IT Manager, AluProfil
- Clara Mendes, Business Analyst, Machines Like Me

---

*[The room has a large window overlooking the extrusion hall. A whiteboard on the
east wall. Coffee and mineral water on a side table. Marco arrives first, already
on his phone. Sabine enters with a stack of paper — actual printouts of customer
PDFs. Thomas comes last, carrying a Lenovo laptop covered in asset-tag stickers.
Clara has set up a notebook and is writing something as they settle in.]*

---

**CLARA:** Guten Morgen, everyone. Thank you for making the time. I know mornings
are tight, especially with the shift changeover at the extrusion lines. I'll keep
us on track and we'll finish by half past ten. I'm Clara Mendes from Machines
Like Me — we specialise in unstructured document intake for industrial ERP
systems. I've read the brief Marco sent over, but I'd really like to hear the
problem from each of you in your own words. Marco, maybe you start?

**MARCO:** Ja, gerne. Also — [he leans back] — we run about four hundred orders a
month through this building. Roughly thirty percent come in electronically,
EDI-FACT, whatever Thomas calls it, straight into MetallSoft. That works. The
other seventy percent — that's almost three hundred orders — come as PDFs.
Attached to emails. From maybe a hundred different customers. And four people sit
in that office — [he points vaguely toward the hallway] — and type them in by
hand. Four full-time clerks. I did the math: thirty percent error rate on
re-keying. Wrong alloy codes, wrong quantities, wrong delivery dates. Every error
costs us — either we make the wrong profile and scrap it, or we miss a date and
the customer calls Sabine screaming.

**SABINE:** They don't scream. Usually. [small smile]

**MARCO:** They complain. Same effect. Point is: we need to automate this. AI
should just figure it out. Read the PDF, pull out the numbers, put them in
MetallSoft. That's what you people do, right?

**CLARA:** [nodding, writing] That's exactly the kind of problem we work on. But
"AI should just figure it out" — I'd like to unpack that a bit. Thomas, you look
like you have thoughts.

**THOMAS:** [adjusting his laptop] I always have thoughts. Marco is right that the
PDF intake is the bottleneck. But — and this is a big "aber" — the system that
receives the data is MetallSoft 7.3. It was installed in 2009. It speaks exactly
one language for inbound orders: UN/EDIFACT ORDERS D.96A. Not XML, not JSON, not
CSV. EDIFACT. And it is — how do I say this diplomatically — intolerant of
mistakes.

**CLARA:** Intolerant how?

**THOMAS:** If a single LIN segment — that's a line item — contains a PIA segment
with an article code that doesn't match an active entry in our Stammdaten, the
entire order is rejected. Not that line. The whole order. All fifty lines, if
there are fifty. Back to the sender. We had Bauprofil send us an order last year
where one line had a code with a trailing space — just a space — and MetallSoft
kicked the entire thing. That's 47 tonnes of aluminum profiles, rejected because
of one whitespace character.

**MARCO:** [waves hand] But that's the current system. The AI should fix the codes
before they get to MetallSoft. That's the whole point.

**THOMAS:** Ja, exactly. The AI needs to get the code 100% right. Otherwise it's
worse than manual entry — at least when Sabine's people type it wrong, they can
fix it line by line. An automated system that generates bad EDIFACT just creates
a different kind of chaos. Faster chaos, but chaos.

**CLARA:** That's a critical constraint. Thomas, could you share your interface
specification document later? I'd like to understand the exact EDIFACT structure.

**THOMAS:** I have it. IT-SPEC-EDIFACT-ORDERS-v3.2. I'll send it after the
meeting. [taps his laptop] It documents every segment, every qualifier, every
validation rule.

**CLARA:** Thank you. Sabine — you brought printouts?

**SABINE:** [spreads several pages across the table] These are from the last three
days. [points to first page] This one is from Bauprofil Bauelemente in Stuttgart.
They're a German construction profile customer, about twelve years now. Very
structured — look at this. DIN-style table. Artikelnummer, Bezeichnung, Menge,
Lieferdatum. Like they read the EDIFACT spec and built a PDF template from it.
Very disciplined. [flips to next page] This one — FensterSystem Alu AG, our Swiss
friends in Schlieren. Semi-structured. Some prose here at the top — "Bitte liefern
Sie folgende Positionen gemäss Rahmenvertrag 2025-03" — and then a table below.
They use calendar weeks. "Lieferwoche 34." They sometimes quote competitor codes
— the old Caprano system from before they switched to us. And everything is in
Swiss francs. [flips again] This one is from ConstruxAlu Façades in Lyon. Very
French. "Nous vous prions de bien vouloir nous livrer les articles suivants" —
very polite, very descriptive, very... not tabular. Half the items here are custom
dies that aren't in our catalog. They write things like "à définir selon
échantillon" — TBD based on sample. And this one — [holds up last page] — Nordic
Aluminium in Stockholm. Minimalist. Sometimes just three columns: a product ID
that's often blank, a description like "40x40x3 L=6000", and a quantity. No alloy,
no temper, no surface. They just... assume we know what they mean.

**MARCO:** So we force them to use a standard form. Problem solved. I've been
saying this for three years.

**SABINE:** [turning to Marco] That's not how it works, Marco. You don't "force"
Bauprofil — we've had that relationship for twelve years. And FensterSystem is our
second-largest PDF customer. You want me to call Hans-Peter Meier and tell him his
format is inconvenient so he should re-tool his entire purchasing system? He'll
call our competitor in Poland and have a quote by Friday.

**MARCO:** I'm not saying be rude about it, but —

**SABINE:** You are saying that. That's exactly what you're saying. "Force them."
These are relationships, Marco. Not data sources.

**MARCO:** [holds up hands] Fine. Fine. So the AI has to handle all the chaos. But
at some point — I still want a human to review every order before it goes into
MetallSoft. I won't sign off on fully automated processing.

**SABINE:** [quietly] Ten minutes ago you said "AI should just figure it out."

**MARCO:** I meant figure out the reading part. The approval is different.

**CLARA:** [diplomatically] So the vision is: AI reads the PDF, extracts the data,
presents a reconciliation screen to an operator, and the operator approves before
it reaches MetallSoft. Is that a fair summary?

**MARCO:** Ja, genau. That's it.

**THOMAS:** Then the operator needs to see two things side by side: what the AI
extracted, and what it resolved to in our catalog. Because the biggest problem —
and Sabine knows this — is matching what the customer wrote to our internal codes.

**CLARA:** Tell me about that matching problem.

**SABINE:** [pulls out another sheet] Here. Look. FensterSystem ordered "ALU 6060
T66" on this line. Our internal code is AE-2018-127 — that's EN AW-6060, temper
T66, which is AlMgSi0.5. Three different names for the same material. And the
customer might write any of them. Sometimes they write "AlMgSi0.5" — the DIN
notation. Sometimes "6060" — the EN numeric. Sometimes just "standard construction
alloy." My clerks have learned to recognise all of these. Can AI?

**THOMAS:** It gets worse. The PIA segment in EDIFACT requires our internal
article number. Not the customer's code. Not the alloy name. Our code —
AE-2018-127 for that specific profile-alloy-temper-length-finish combination. So
the matching isn't just material mapping — it's profile geometry, alloy, temper,
length, and surface finish, all resolved to one internal code.

**CLARA:** How many internal codes are there?

**THOMAS:** We have thirty-five standard profiles in the catalog, each available
in four alloys with two or three tempers, various lengths, and several surface
finishes. That's maybe two thousand active SKUs. Plus customer-specific dies —
that's another few hundred. MetallSoft has the authoritative list. If it's not in
the Stammdaten, the order won't process. Period.

**CLARA:** And Sabine, you mentioned ConstruxAlu sends custom die orders. Items
that aren't in your catalog at all?

**SABINE:** Ja, constantly. They'll order a profile that we designed specifically
for their "Façade 3000" system — our internal code might be AE-2024-034 — but
sometimes they're ordering something entirely new. A custom die that doesn't exist
yet. They'll write "profilé spécial selon plan client réf. PLAN-2025-081" — "per
customer drawing." In that case, there is no internal code. We have to create one.
We have to enter it into MetallSoft first, get it approved by engineering, and
then process the order. That usually takes three to five days. If the AI just sees
an unknown code and rejects it, we lose the order.

**THOMAS:** And if it invents a code and sends it to MetallSoft, the whole order
bounces. So the operator needs a way to flag "this item needs a new article
master" and put the order on hold.

**MARCO:** But in the happy path — the standard profiles with known codes — it
should fly through. One click approve.

**SABINE:** [leafing through her stack] Here's another thing that happens. See
this Bauprofil order? Line 4: "Menge: 50." Fifty what? Pieces? Meters? Kilograms?
The unit is supposed to be in the next column — "Einheit" — but here it's blank.
It's blank, Marco. What does the AI do with that?

**MARCO:** It asks the operator?

**SABINE:** But what if the operator doesn't know either? Because in this case —
[she squints at the paper] — I know this customer. They order profile AE-2015-088
in standard 6-meter lengths. So "50" means fifty pieces at 6 meters each — 300
meters total. But if you didn't know this customer, you'd have to call them. My
clerk Anna did call them. That's why this order didn't ship wrong. An automated
system would have shipped... who knows? Fifty meters? Three pieces?

**THOMAS:** In EDIFACT, the QTY segment always has a qualifier — QTY+21 means
ordered quantity — and the unit comes from the IMD segment or the article master.
But if you're extracting from a PDF where the unit is missing, you have to infer
it. And inference is where errors happen.

**CLARA:** [writing steadily] So the system needs customer-specific defaults. Or
it needs to flag ambiguity and ask. What other edge cases do you see regularly?

**SABINE:** Alloy substitutions. This happens maybe twice a month. We run out of
6060 — say the billet delivery from our supplier in Norway was late — so we
substitute 6063. Almost identical mechanical properties. T6 temper. Most customers
accept it. But some don't — especially structural applications where the slight
strength difference matters. My team handles this by calling the customer and
getting a verbal approval, then noting it in the system. But there's no field for
"customer approved substitution" in the PDF. It's tribal knowledge.

**CLARA:** How would you want the system to handle substitutions?

**SABINE:** Ideally? The system detects that an order item can't be fulfilled in
the requested alloy, suggests an alternative, and generates an email to the
customer. "We're out of 6060 T6, can we ship 6063 T6 instead? Please reply to
approve." Approval gets logged against the order line. Only then does the order
proceed.

**MARCO:** [frowning] That sounds complicated. Can it just flag it for the
operator and let them make the call?

**SABINE:** That's what we do now. The operator — me, usually — spends twenty
minutes on the phone with the customer, clarifies the substitution, writes an
email confirmation, forwards it to Thomas so he can manually adjust the order
in MetallSoft. It's twenty minutes for one line item. If the system could
automate the communication and only escalate when the customer says no — that
would save me hours every week.

**THOMAS:** From an IT perspective, substitution means we need inventory
visibility. MetallSoft knows current stock levels, but only for finished profiles.
Billet inventory is in a separate system — the production planning module. If the
AI needs to know that 6060 billets are low before the order even arrives, it needs
to talk to both systems.

**CLARA:** That sounds like a Phase 2 feature. Let's keep it in the requirements
backlog but not in the prototype.

**MARCO:** Agreed. Prototype should focus on reading the damn PDFs first.

**CLARA:** Thomas, you mentioned earlier that the big customers send EDIFACT
directly. Are any of the PDF customers also sending structured data alongside
their PDFs?

**THOMAS:** [pause — he glances at Marco, then at Sabine] That's... actually
something I've been meaning to bring up. Some of these PDFs — not all, but some —
were generated by the customer's own ERP system. And when you look inside them —

**MARCO:** What do you mean "look inside them"?

**THOMAS:** When you examine the actual file, not the printed page. I discovered
this about eight months ago when I was troubleshooting a font rendering issue with
one of the Swiss orders. The PDF — from FensterSystem — it has embedded metadata.
JSON, actually. Attached as what the PDF spec calls "piece info" metadata. The
customer's ERP — it's an Abacus system, I think — it generates the PDF for human
reading but also embeds structured data.

**SABINE:** [leaning forward] Wait. You're saying the data is already in the PDF?
Digitally?

**THOMAS:** Not in all of them. FensterSystem — yes. Bauprofil — yes, but in a
different schema. ConstruxAlu — sometimes, but the JSON is in French field names.
"référence_article", "quantité", "date_livraison_souhaitée." Nordic Aluminium —
rarely. Their PDFs are usually scanned. But the point is: for maybe forty percent
of the incoming PDFs, the structured data is already sitting there. Nobody
bothered to look.

**MARCO:** [staring at Thomas] You've known this for eight months?

**THOMAS:** I mentioned it in the IT status report. June 2025. Section 4.3.

**MARCO:** Nobody reads the IT status report, Thomas. That's — [he exhales] —
okay. So we've had structured data sitting in these PDFs and four people are
re-typing them. That's exactly why we need an outside perspective. [to Clara]
This is what I mean. We're — we're not seeing what's right in front of us.

**SABINE:** [looking at her printouts with new eyes] So for FensterSystem, the
JSON says... what fields?

**THOMAS:** [opening his laptop] I have an extract. Let me pull it up. [pause,
typing] Here. For a typical FensterSystem order, the embedded JSON contains
something like:

```
{
  "order_ref": "FS-2026-0417",
  "order_date": "2026-05-28",
  "items": [
    {
      "art_code": "PRO-045-0020",
      "description": "Fensterprofil Rahmen 60mm, EN AW-6060 T66, EV1",
      "qty": 120,
      "uom": "PCE",
      "delivery_week": 34,
      "alloy": "EN AW-6060",
      "dimensions": "60x40x2 L=6000"
    }
  ]
}
```

**SABINE:** [looking over his shoulder] That "art_code" — PRO-045-0020 — that's
their internal code. Not ours.

**THOMAS:** Exactly. So even with structured JSON, we still need to map their
codes to our AE- prefixed codes. But the JSON gives us clean, unambiguous fields
— no OCR, no layout parsing, no guessing whether "50" means pieces or meters.
It's a much cleaner starting point.

**CLARA:** That's significant. The prototype should absolutely leverage embedded
JSON metadata when it's available, and fall back to layout parsing when it's not.
Thomas, can you share sample PDFs with embedded JSON — sanitised, of course — so
we can build test fixtures?

**THOMAS:** Ja, I can prepare a packet. I'll need to clear it with our
Datenschutzbeauftragten — data protection officer — but for internal development
use it should be fine. I'll replace the customer names and prices with dummy data.

**CLARA:** Perfect. Now — Sabine, you mentioned earlier that sometimes the JSON
metadata in the PDF disagrees with the visible text. Can you say more about that?

**SABINE:** Oh — that wasn't me. That was Thomas who discovered the JSON.

**THOMAS:** Right. There's an edge case, Clara — I've seen it twice now — where
the embedded JSON has different data than the human-readable table in the PDF.
Same order. The table says 200 pieces, the JSON says 180. We don't know which is
authoritative. Is the JSON generated first, and then the PDF template was edited
manually? Or vice versa? It's a reconciliation problem even before we get to
MetallSoft.

**SABINE:** [nodding vigorously] This is exactly what I mean about not trusting
automation blindly. If the system picked the JSON number and didn't show the
operator the original PDF, we'd ship 180 instead of 200, and FensterSystem would
be short twenty pieces for their window production line in Zurich. Then I get a
call from Herr Meier at seven in the morning.

**CLARA:** So the reconciliation screen must show both sources side by side. The
original PDF image — or at least a snippet — next to the extracted data. And if
there's a discrepancy between metadata and visual text, it should be flagged
prominently.

**MARCO:** Flagged — but not blocked. If the operator can resolve it with one
click, fine. If it requires a phone call to Switzerland, that's also fine. But
don't let it hold up the other forty-nine lines.

**THOMAS:** That's the hard part, Marco. MetallSoft doesn't do partial processing.
Remember what I said — entire order accepted or rejected. So if line 37 has a
discrepancy that requires a customer call, what happens to lines 1 through 36 and
38 through 50? We can't post those to MetallSoft while we're waiting for
clarification.

**CLARA:** Could the system split the order? Extract the clean lines, post them,
and hold the disputed lines in a separate queue?

**THOMAS:** [thinks for a moment] Technically possible, but it would violate the
customer's expectation. They sent one order. If we partially post it, their system
gets a partial order confirmation — ORDRSP in EDIFACT terms — and they don't know
that line 37 is on hold. It creates a reconciliation nightmare on their side too.

**SABINE:** In practice, what we do now: we call the customer immediately. If it's
a small discrepancy, we resolve it verbally and post the whole order. If it's a
big one, we hold the entire thing. Better to delay everything by four hours than
to ship wrong.

**MARCO:** So the system needs to support both. Quick resolution workflow — fix
the line and approve. And complex resolution workflow — put the whole order on
hold and alert Sabine's team.

**CLARA:** [finishing a note] That's a good requirement. Let me summarise what
I've captured as the core workflow. Please push back if I've misunderstood. [She
turns her notebook so they can see.]

1. PDF arrives by email — either as attachment or via a dedicated mailbox.
2. System ingests the PDF. If embedded JSON metadata is present, extracts it
   as the primary structured source. If not, performs layout parsing and OCR.
3. For each line item, the system attempts to resolve the customer's description
   — alloy, profile, dimensions, temper, finish — to an internal MetallSoft
   article code (the AE- prefix codes).
4. Data goes to a reconciliation screen where the operator sees:
   - The original PDF (or snippet) on one side
   - Extracted fields on the other side
   - The resolved internal code (or a warning if no match)
   - Flagged discrepancies: JSON vs visible text, missing units, unknown codes
5. Operator can correct, approve, or escalate each item.
6. On approval, the system generates EDIFACT ORDERS D.96A and posts to
   MetallSoft.
7. On rejection by MetallSoft — invalid PIA code, etc. — the order returns to
   the operator with the specific error.

Does that sound right?

**MARCO:** Ja. That's what I had in mind. [pause] Except I thought step 5 would
be more... automated. Review takes time.

**SABINE:** Review is the only thing that prevents the 30% error rate from
becoming a 100% error rate, just faster. If you want to reduce review time, you
need to increase the system's confidence. High-confidence lines get a green check
— operator glances and clicks approve. Low-confidence lines get a red flag —
operator investigates. That's the right balance.

**THOMAS:** And "confidence" needs to be real, not artificial. A machine learning
model that says "92% confidence" because it doesn't know what it doesn't know is
worse than useless. The confidence metric has to reflect actual risk: unmatched
codes, ambiguous units, metadata discrepancies, unknown alloys.

**CLARA:** Absolutely. Confidence scoring based on concrete signals, not just
model output probabilities. Thomas, on the EDIFACT side — you said you'd share
the spec. What's the one thing in that spec that you think will cause us the most
trouble?

**THOMAS:** [without hesitation] The PIA segment. Specifically PIA+1 with
qualifier SA — supplier's article number. That's the field that MetallSoft
validates against the Stammdaten. Every other segment — IMD, QTY, MEA, DTM —
those are informative. They can be wrong and the order still posts; they just
show up wrong in production planning and someone catches it later. But PIA+1 is
the gate. Wrong code, no entry. And some of our customers — like Nordic Aluminium
— they don't even use our codes. Their prod_id field is frequently empty. Sabine's
team has to manually look up the item by description and dimensions, find the
internal code, and enter it. That's the single hardest step to automate.

**CLARA:** And for the prototype that you want to see at the next meeting — is
PIA matching in scope or out of scope?

**THOMAS:** In scope. Without it, the prototype doesn't demonstrate an end-to-end
flow. Even if the matching is naive — exact string match on a mapping table, say
— it needs to show the concept.

**MARCO:** Agreed. Show me a PDF going in, data coming out, an operator clicking
approve, and an EDIFACT file appearing. That's what I need to see.

**SABINE:** [gathering her printouts] And show me that it can handle Bauprofil.
If it can handle their structured tables — that's the easy case. And then show me
ConstruxAlu — the French prose — that's the hard case. If it can do both, I'll
believe this might work.

**CLARA:** We'll prepare a prototype that covers both. What about timeline? When
can we reconvene?

**MARCO:** Two weeks? Is that realistic?

**CLARA:** For a functional prototype with the core reconciliation screen — yes.
It won't be production-ready. No substitution logic, no email integration, no
inventory checks. But you'll see a PDF ingested, data extracted, operator review,
and EDIFACT output. We can iterate from there.

**SABINE:** I'll prepare sample PDFs from all four customers. Bauprofil,
FensterSystem, ConstruxAlu, Nordic. Sanitised.

**THOMAS:** I'll send the EDIFACT spec and the article master export today. And
those PDFs with embedded JSON.

**MARCO:** [standing] Gut. Clara, I appreciate the structured approach. This is
more — [he searches for the word] — gründlich than I expected. Thorough. [small
smile] Better than "AI should just figure it out."

**CLARA:** [smiling] I'll take that as a compliment. We'll send a calendar invite
for the prototype review. Same room?

**MARCO:** Same room. Sabine, bring more printouts. Thomas — [pointing at him] —
no more secrets in the IT status report. If you find something, tell us.

**THOMAS:** [closing his laptop] I'll send a summary email. Not an IT status
report. [pause] A normal email.

**SABINE:** [to Clara, quietly, as they're packing up] The JSON thing — that's
been sitting there for eight months. If you can build a system that actually uses
it, you'll have solved half the problem before you even start on the AI part.

**CLARA:** Sometimes the biggest wins aren't the AI. They're the plumbing. I'll
see you all in two weeks.

---

*[Meeting ends 10:31. Sabine and Clara walk out together discussing the French
PDF formats. Thomas stays behind to write something in his laptop — possibly that
summary email. Marco is already on his phone, but he pauses at the door and looks
back at the whiteboard, where Clara has sketched the workflow. He nods once, then
leaves.]*

---

## Clara's Raw Notes (typed immediately after meeting)

- **Primary goal:** PDF-to-EDIFACT pipeline for MetallSoft 7.3
- **Volume:** ~300 PDF orders/month, 4 clerks, 30% error rate on re-keying
- **EDIFACT format:** UN/EDIFACT ORDERS D.96A (ref: IT-SPEC-EDIFACT-ORDERS-v3.2)
- **Critical constraint:** MetallSoft rejects ENTIRE order if any PIA+1 code is
  unmapped — no partial processing
- **Four customer formats:**
  1. Bauprofil (DE) — structured DIN-style tables, German JSON metadata
  2. FensterSystem (CH) — semi-structured, calendar weeks, Swiss francs,
     Abacus ERP with embedded JSON
  3. ConstruxAlu (FR) — descriptive/prose, many custom dies, French JSON metadata
  4. Nordic Aluminium (SE) — minimalist, often by dimensions instead of codes,
     sometimes scanned PDFs (no embedded data)
- **Embedded JSON:** Present in ~40% of PDFs (FensterSystem, Bauprofil,
  sometimes ConstruxAlu). Fields vary by customer. Discovered by Thomas 8 months
  ago but not leveraged.
- **Edge cases:**
  - Quantity ambiguity (pieces vs meters vs kg)
  - Alloy aliases (6060 = AlMgSi0.5 = EN AW-6060)
  - Custom dies not in catalog (need new article master creation)
  - Call-off orders with multiple delivery dates per order
  - Alloy substitutions (6060→6063) with customer approval tracking
  - Metadata vs visible text disagreement (JSON says 180, table says 200)
  - Missing prod_id — must resolve by description + dimensions
- **Reconciliation screen requirements:**
  - Show original PDF snippet + extracted data side by side
  - Flag discrepancies (JSON vs visual, missing units, unknown codes)
  - Show resolved internal code with confidence indicator
  - Support quick fix (in-line edit) and escalation (hold order)
- **Prototype scope (2 weeks):**
  - PDF ingestion for Bauprofil (easy) and ConstruxAlu (hard)
  - Leverage embedded JSON where available, fall back to parsing
  - Naive code matching (exact string on mapping table)
  - Operator reconciliation screen with approve/reject
  - EDIFACT ORDERS D.96A output generation
  - OUT OF SCOPE: substitution logic, email integration, inventory checks,
    customer-specific defaults
- **Next meeting:** prototype review, same room, ~2 weeks
- **Action items:**
  - Thomas: send EDIFACT spec + article master export + sample PDFs with JSON
  - Sabine: prepare sanitised sample PDFs from all 4 customers
  - Clara: build prototype

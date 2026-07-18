# Founder OS v2.2.0 — przegląd projektu (2026-07-18)

> **Status wdrożenia (2026-07-18):** B1–B6 naprawione; testy hooka (outbound, allow-paths, fail-open, fallback parser), test end-to-end realnego pakietu i `check_readme_counts` w walidatorze dodane; doctor ma check #13 (queue rotting) i tolerancję sufiksów dat; template sankcjonuje `## Named failure modes`; drobiazgi (working day, 5 business days, guardrails desc, CLAUDE.md shorthand, cross-ref rate/pricing, annual-review u stratega) wprowadzone. B4 rozwiązane przez usunięcie `Agent(board-member)` u stratega (spoken handoff, zgodnie z house rule 4). Stan: walidator 14 checków / 0 błędów, 75 testów zielonych (było 57). Nie ruszone (decyzje produktowe): standaryzacja `## Refusals`, `model:` pins, publikacja marketplace + `<owner>` w README.

**Werdykt:** pakiet jest w bardzo dobrym stanie (walidator: 12 agentów / 48 skills / 0 błędów, 57 testów zielonych), ale ma 6 realnych nieścisłości — z czego 3 to dokładnie klasa błędu, przed którą projekt sam ostrzega ("stale count / second map") — oraz kilka luk w testach hooka.

Ground truth: `python3 scripts/validate_package.py founder-os` → `12 agent(s), 48 skill(s), 0 error(s)`; `python3 -m unittest discover -s tests` → 57 OK. Liczby z README (48 skills, 12 agentów, 9 cadences) zweryfikowane na dysku — zgadzają się.

---

## 1. Bugi / nieścisłości

### B1. README kłamie o allowlistach narzędzi
`README.md:138-141`: *"Their tool allowlists are `Read, Write, Edit, Glob, Grep` and nothing else."*
Stan faktyczny: 5 agentów ma dodatkowo `Agent(...)` (chief-of-staff ×11, strategist, delivery-lead, focus-coach, positioning-advisor), a `board-member` ma **mniej** (`Read, Glob, Grep` — bez Write/Edit). `house-rules.md` reguła 4 i `ALLOWED_AGENT_TOOLS` w walidatorze znają `Agent` — README nie.
**Fix:** przepisać na faktyczne twierdzenie bezpieczeństwa: "żaden agent nie ma Bash, WebFetch ani narzędzia MCP" (to jest prawdziwe i to jest sedno). Wyliczenie usunąć albo urealnić.

### B2. README: "The eight skills that record what someone outside told you"
`README.md:113`. Nigdzie nie ma listy tych ośmiu; `ingestion-gate` jest skillem uniwersalnym ("Every agent carries this skill") i ingestujących skilli jest znacznie więcej niż 8. Prawdopodobnie konfuzja z inną ósemką — "Eight cadences propose" (proposer set w `queue`/`daily-brief`). To dokładnie anty-wzorzec, który `ownership.yaml:76-79` wyśmiewa ("The last one said 'ten' and stayed at ten").
**Fix:** count-free: "Every skill that records what someone outside told you…".

### B3. `founder-os-init`: "The eight cadences" — jest dziewięć
`skills/founder-os-init/SKILL.md:146` vs `setup-cadences` ("nine cadences", tabela 9 wierszy) i README (`Cadences | 9`). Relikt sprzed dodania `calendar-audit`.
**Fix:** "nine" albo count-free.

### B4. Graf `Agent()` niespójny z org-chartem i z własną regułą
`strategist` ma `Agent(board-member)` (`agents/strategist.md:12`) — ale w `org-chart.mmd` board-member wisi pod Founderem, nie pod strategiem. Jednocześnie `positioning-advisor.md:71-73` jest explicite trzymany za mordę: "handoff outside your list is spoken, not spawned" — czyli ta sama sytuacja, odwrotne traktowanie. Dodatkowo chart nie pokazuje skip-level reach chief-of-staffa (11 agentów vs 4 krawędzie na diagramie).
**Fix:** albo dodać krawędź ST→BM do `org-chart.mmd` (i zaakceptować, że strateg "zarządza" board-memberem), albo wyciąć `Agent(board-member)` u stratega i zrobić z tego spoken handoff. Skip-level COS oznaczyć w chartcie (przerywane krawędzie / legenda).

### B5. `context-load` krok 5 przeczy skillom, które sam wymienia
Cap "dwa pliki ponad trójkę charter/goals/metrics" z jedynymi wyjątkami `triage` i `daily-brief` — a `monthly-review` czyta +4 pliki, `weekly-review` +3, `week-plan` +3. Skille są nazwane jako związane capem i z definicji go łamią.
**Fix:** dopisać obustronne, nazwane wyjątki (jak ma `triage`) albo zluzować sformułowanie capu.

### B6. Fałszywa przesłanka w `outreach-draft` / `proposal-draft`
Oba uzasadniają per-deal `Proposed:` tym, że "pozostała piątka to cadences emitujące **jedną** linię" — a `revenue-review` emituje do 4 linii `Proposed:`, `quarterly-planning` do 3. Wniosek dobry, uzasadnienie fałszywe, zduplikowane w dwóch plikach.
**Fix:** przepisać na prawdziwą oś: per-period vs on-demand-repeatable.

---

## 2. Luki w testach (działają, ale nie dowodzą tego, co najważniejsze)

- **`check_outbound` w hooku ma zero pokrycia.** Cała połówka House Rule 0 (deny dla `Bash`/`WebFetch`/`mcp__*` u subagenta) — nieprzetestowana, mimo że sam hook argumentuje, że to guard #2 trzyma granicę. Regresja matchera wyjdzie cicho.
- Brak testu pozytywnego: właściciel pisze własny plik → allowed.
- Brak testów fail-open (brak mapy → allow, śmieci na stdin → allow) i fallback-parsera `_parse_owns_without_yaml` (spory ręczny parser, 0 testów).
- Brak testu end-to-end: nic nie asseruje, że **realny** pakiet przechodzi wszystkie `CHECKS` z 0 błędów (tylko `check_hooks` dotyka prawdziwego drzewa). Akceptacyjne "12/48/0" jest ręczne, nie wykonywalne.
- Gałąź `re.error` ("matcher is not a valid regex") w `check_hooks` — niepokryta.

---

## 3. Obserwacje (spójne, ale warte świadomości)

- **Nikt nie ma `Skill` w `tools:`**, a prozy każą "run `queue`", "run `voice-capture`" itd. Jeśli inwokacja skilla z poziomu subagenta wymaga narzędzia `Skill`, to systemowa dziura w 12 plikach; jeśli `skills[]` w frontmatter wystarcza — non-issue. **Do zweryfikowania empirycznie** (walidator dopuszcza `Skill` w `ALLOWED_AGENT_TOOLS`, co sugeruje, że kiedyś było/miało być).
- Delegacja "run `queue`": `daily-brief`/`triage`/`weekly-review` piszą do `queue.md` przez skill `queue`, nie deklarując `queue.md` w swoich `writes` — spójna konwencja (ten sam agent-właściciel), ale walidator jej nie widzi.
- `## Refusals` w 7 z 12 agentów — brak u chief-of-staffa (najwyższe uprawnienia) przy obecności u agentów jednoplikowych. Wygląda na arbitralne, nie na decyzję.
- `annual-review` jest w `skills[]` stratega, ale ciało agenta opisuje wyłącznie pracę kwartalną — roczny przegląd nie ma opisanego zachowania w prozie agenta.
- Cron `revenue-review` (`0 9 1 * *`) i `quarterly-planning` odpalają 1. dnia kalendarzowego, a proza mówi "first **working** day".
- `daily-brief` "5 days" vs `win-loss-analysis` "5 **business** days" — drobna rozbieżność jednostki.
- Decyzja "zwolnić klienta" nie ma jednego właściciela (CFO flaguje ekonomię, delivery-lead delivery, obaj logują przez COS) — implicite founder, ale żadna linia "You decide…" tego nie niesie.
- Cena w dwóch plikach: `offer.md ## Pricing` (positioning-advisor) vs `metrics.md ## Rate` (CFO) — rozmyślny split, ale bez cross-reference; ryzyko dryfu.
- CLAUDE.md/README używają skrótu `drafts/`, `reviews/` zamiast subdirów z mapy — nieszkodliwe (CLAUDE.md sam mówi "the map wins", `owner_of` nie matchuje gołego `drafts/`), ale warte doprecyzowania.
- v2.2 plan: wszystko w repo dowiezione; **poza repo niezweryfikowalne**: publikacja (`marketplace.json`, `~/founder-os-public/`), `<owner>` w instrukcji instalacji w README nadal literalny — instalacja przez obcego jeszcze nie działa, a to był główny cel v2.2 wg speca.
- Najsłabsze beliefs (wciąż nad progiem, ale generyczne): `skill-gap` ("Two gaps closed is zero"), `week-plan`/`daily-brief` (zduplikowany aforyzm "a plan with no cost is a wish"), `learning-plan` (mainstreamowy deliberate-practice).

---

## 4. Usprawnienia / nowe rzeczy (priorytetyzowane)

1. **Fixy B1–B6** — wszystkie to edycje prozy/jednego pliku, zero ryzyka. Największy zwrot: B1 (README to twarz pakietu, a zdanie o allowlistach jest falsyfikowalne w 10 sekund przez każdego recenzenta).
2. **Testy hooka** (sekcja 2) — `check_outbound` deny, owner-allow, fail-open, plus jednolinijkowy test `run_checks(real_root) == []`. To zamyka realną dziurę regresyjną najtaniej, jak się da.
3. **`check_readme_counts` w walidatorze** — README table (12/48/9) i wyliczenia to dokładnie "second map"; skoro pakiet machine-checkuje wszystko inne, counts też powinien. Alternatywnie: usunąć liczby z README w ogóle, zgodnie z własną filozofią count-free.
4. **Queue-health w `founder-os-doctor`** — capy (`## Doing` ≤3, `## Queued` ≤15) i zegary (21/14/5 dni) egzekwuje wyłącznie piątkowy sweep `weekly-review`; jak sweep stanie, kolejka gnije niewidzialnie, mimo że doctor i tak czyta cały workspace. Tani, wysokowartościowy check nr 13.
5. **Ujednolicić handoffy**: konwencja "spawned vs spoken" z positioning-advisora do wszystkich sekcji "Who you hand off to"; zdecydować o `## Refusals` (obowiązkowe albo jawnie opcjonalne); dodać `## Named failure modes` do `skill-template.md` jako sankcjonowany opcjonalny nagłówek (używa go 15 skilli, template go nie zna).
6. **Doprecyzować w doctorze tolerancję sufiksów dat** w section-drift check ("## Close — 2026-07"), żeby implementacja literalna nie sypała false positives.
7. **Rozważyć `model:` per agent** — board-member (red-team/premortem) i chief-of-staff (fanout ×11) to naturalni kandydaci na jawny pin zamiast dziedziczenia defaultu.
8. **Dokończyć v2.2 poza repo**: publikacja marketplace + podmiana `<owner>` w README — bez tego instrukcja instalacji jest martwa.

---

*Zakres: pełny odczyt rdzenia (README, CLAUDE.md, hook, walidator, references), audyt 48 SKILL.md + 12 agentów + docs/tests przez 3 subagentów, weryfikacja kluczowych findingów grepem i uruchomieniem walidatora/testów. Nic nie modyfikowano.*

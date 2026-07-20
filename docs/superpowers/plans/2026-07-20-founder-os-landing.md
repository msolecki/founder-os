# Founder OS — sprzedażowy landing page

Status: gotowe z jawnym ograniczeniem review
Data: 2026-07-20

## Cel

Zbudować samodzielną polską stronę HTML, która wyjaśnia osobie prowadzącej
firmę solo, czym jest Founder OS, jak używa się go w praktyce i dlaczego jest
czymś więcej niż kolejnym czatem z AI.

## Decyzje

- Format: jeden plik `site/index.html`, bez buildu i zależności.
- Odbiorca: founder firmy usługowej, konsultant lub właściciel kilku małych
  biznesów, który pracuje w Claude Code.
- Główna obietnica: Founder OS zamienia rozproszone rozmowy z AI w pamiętający
  stan firmy zespół wykonawczy, który pilnuje decyzji i rytmu pracy.
- Dowody produktowe: 13 agentów, 49 workflowów, 10 kadencji, lokalny stan w
  Markdown, ownership guard, brak wysyłania i płacenia przez agentów.
- CTA: instalacja pluginu; bez ceny i formularza, bo repo nie definiuje oferty
  płatnej ani modelu sprzedaży.
- Styl: editorial command center — ciepłe tło, granat, elektryczny pomarańcz,
  mocna typografia, interfejs operacyjny zamiast stockowych zdjęć.

## Krok 1 — narracja i architektura informacji [S]

**What:** Ułożyć ścieżkę od problemu foundera przez mechanizm produktu do
instalacji.

**Where:** Ten plan oraz copy w `site/index.html`.

**How:** Hero → koszt chaosu → różnica Founder OS → dzień/tydzień pracy →
zespół → mechanizm pamięci i bezpieczeństwa → FAQ → instalacja.

**Test:** Każda obietnica sprzedażowa ma oparcie w `founder-os/README.md`,
`founder-os/COMMANDS.md` albo kanonicznym `founder-os/CLAUDE.md`.

## Krok 2 — implementacja strony [M]

**What:** Responsywny, dostępny landing z lekkimi interakcjami.

**Where:** `site/index.html`.

**How:** Semantyczny HTML, inline CSS, vanilla JS; bez zewnętrznych fontów,
frameworków i skryptów. Dodać mobilną nawigację, przełączany podgląd briefu,
kopiowanie komend, FAQ w `details` i animacje respektujące
`prefers-reduced-motion`.

**Test:** Dokument ma poprawną strukturę nagłówków, widoczny focus, działa bez
JS i nie ma poziomego overflow przy szerokości 375 px.

## Krok 3 — walidacja [M]

**What:** Sprawdzić stronę oraz brak regresji pakietu.

**Where:** `site/index.html` i repozytorium.

**How:** Parser HTML, kontrola linków/ID, uruchomienie strony lokalnie,
screenshot desktop/mobile, `python3 scripts/validate_package.py founder-os`
oraz `python3 -m unittest discover -s tests`.

**Test:** Brak błędów parsera i linków wewnętrznych; oba testy repo przechodzą;
screenshot potwierdza układ desktop i mobile.

## Krok 4 — świeży review [S]

**What:** Niezależny przegląd końcowego HTML i poprawki po review.

**Where:** `site/index.html`.

**How:** Świeży subagent otrzyma wyłącznie cel, ścieżkę, ograniczenia i format
wyniku; po jego werdykcie zmiany zostaną zweryfikowane lokalnie.

**Test:** Brak nierozwiązanych usterek wysokiej lub średniej wagi.

## Inwariant

Landing jest dodatkiem do repo i nie zmienia działania ani instalacji pluginu.
Istniejące, niezwiązane zmiany w hookach i testach pozostają nietknięte.

## Następny krok

Zwalidować `site/index.html` na desktopie i mobile, uruchomić testy pakietu,
a następnie przekazać stronę do świeżego review.

## Postęp

- 2026-07-20: ukończono narrację i architekturę informacji.
- 2026-07-20: ukończono samodzielny landing HTML/CSS/JS.
- 2026-07-20: parser HTML, kontrola ID/anchorów/ARIA i parser JavaScript
  przeszły; walidator pakietu zgłosił 13 agentów, 49 skilli i 0 błędów; 80
  testów unit przeszło.
- 2026-07-20: audyt kontrastu wykrył i naprawił drobny tekst na pomarańczowym
  tle; dodano też działającą bez JavaScript mobilną nawigację.
- 2026-07-20: Chrome headless kończył się kodem 134, a lokalny serwer był
  blokowany przez profil wykonawczy, więc screenshot desktop/mobile nie powstał.
- 2026-07-20: dwie próby świeżego review subagentem zablokował aktywny
  `ownership-guard.py`, który w Codex klasyfikuje read-only terminal jako
  outbound `Bash`. Nie obchodzono guarda ani nie modyfikowano hooków; wykonano
  końcowy audyt lokalny, a ograniczenie pozostaje jawne w handoffie.

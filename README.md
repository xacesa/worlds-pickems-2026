# WORLDS 2026 · Judith × Tony × Alex

Private League of Legends Worlds Pick’ems mit 18 Fragen aus eurer PDF und Tagesständen von [PEM.LOL](https://pem.lol/worlds/2026/pickems).

## Was funktioniert?

- Alle 18 Tipps, Filter, Suche und Bestenliste auf Handy und Desktop.
- `results.json` enthält die aktuellen **Zwischenstände** in `live` und **endgültig bestätigte** Antworten in `results`.
- Zwischenstände sind informativ und geben **keine Punkte**. So wird z. B. ein vorläufiges „Nein“ bei Teemo nicht vorschnell als korrekt bewertet.
- `sync_pem.py` ist der konservative Parser für die öffentliche PEM.LOL-Webseite.
- `.github/workflows/sync-and-deploy.yml` ruft PEM.LOL einmal täglich ab (07:15 UTC, das entspricht 08:15 Uhr MEZ / 09:15 Uhr MESZ), schreibt `results.json` und veröffentlicht die Webseite auf GitHub Pages. GitHub kann geplante Läufe verzögert starten.
- Bereits erkennbare, unumkehrbare „Ja“-Ereignisse (Faker 700 Kills, Teemo-Pick, LCS in Knockouts, 15 Kills, 450 CS) werden automatisch finalisiert. Übrige Resultate werden erst nach dem geplanten Turnierende und eindeutigen Bestätigungssignalen auf PEM.LOL bewertet. Bei Zweifelsfällen bleibt die Frage offen.
- **Frage 18:** PEM.LOL zeigt das kürzeste Spiel und die Paarung, aus diesem Text allein ist nicht zweifelsfrei der Gewinner erkennbar. Für den finalen Punkt kann eine einmalige manuelle Ergänzung in `results.json` nötig sein.

## Öffentlich veröffentlichen (kostenlos mit GitHub Pages)

1. Ein öffentliches GitHub-Repository erstellen, z. B. `worlds-pickems-2026`.
2. Den **Inhalt dieses Ordners** (inklusive des versteckten Ordners `.github`) auf den Branch `main` hochladen und committen. Das ZIP selbst nicht als einzelne Datei hochladen.
3. Im Repository unter **Settings → Pages** als Source **GitHub Actions** auswählen.
4. Unter **Settings → Actions → General → Workflow permissions** den Workflowzugriff **Read and write permissions** erlauben. Wenn die Option organisatorisch gesperrt ist, kann der Bot nicht in `results.json` schreiben.
5. Unter **Actions → Worlds Pick'ems aktualisieren → Run workflow** den ersten Lauf manuell starten. Der Job lädt Daten und veröffentlicht die Website.
6. Die öffentliche Adresse steht anschließend unter **Settings → Pages**. In der Regel `https://GITHUBNAME.github.io/worlds-pickems-2026/`.

Danach aktualisiert GitHub Actions **einmal pro Tag die zentrale JSON-Datei** und verteilt sie über GitHub Pages. In offenen Browsertabs schaut die Webseite alle 30 Minuten nach dem neuesten Stand.

Alternativ können die Dateien auf Vercel veröffentlicht werden, wenn das Repository dort verbunden wird. In diesem Fall aktualisieren Änderungen von GitHub Actions an `results.json` die Vercel-Seite durch erneutes Deployment.

## Parser lokal ausführen

```sh
python -m pip install -r requirements.txt
python sync_pem.py
```

Bei Änderungen am Aufbau der Datenquelle bricht die Aktualisierung im Zweifel mit Fehler ab, statt willkürliche Resultate zu vergeben. Das Skript greift auf die öffentliche Webseite zu, benutzt keine privaten Zugänge und ist **kein offizieller Riot-Endpunkt**. Bitte die Nutzungsbedingungen von PEM.LOL vor dem dauerhaften Betrieb prüfen. Der tägliche Abruf wurde hier anhand der sichtbar abrufbaren Inhalte vorbereitet, aber ein Live-HTTP-Abruf des Skripts war in dieser Arbeitsumgebung nicht möglich. Den ersten GitHub-Workflow-Lauf deshalb prüfen.

## Manuelle Ergänzungen

Für finale, geprüfte Ergebnisse kann `results.json` direkt bearbeitet werden. Beispiel:

```json
{
  "format": "worlds-2026-results",
  "version": 1,
  "updatedAt": "2026-11-15T18:00:00Z",
  "sourceUrl": "https://pem.lol/worlds/2026/pickems",
  "results": {"12": "Ja", "18": "Gen.G"},
  "live": {}
}
```

Die automatisierte Aktualisierung erhält vorhandene finale Ergebnisse und verweigert widersprüchliche automatische Überschreibungen. Eigene Eingaben im Bearbeitungsmodus der Webseite liegen nur lokal im Browser und ändern **nicht** die gemeinsame Datei. Die IDs 1–18 entsprechen den Fragen der PDF.


## Swiss Stage: Acht Weiterkommen-Tipps pro Person

Die Webseite hat zwei Bereiche: **Crystal Ball** und **Swiss Stage**. Im Swiss-Tab stehen die drei Pick'em-Karten für Judith, Tony und Alex über dem Spielplan.

Jede Person tippt genau **acht verschiedene Teams**, die in die K.-o.-Phase einziehen: ein Team mit 3:0, ein Team mit 3:1, ein Team mit 3:2 und fünf weitere qualifizierte Teams ohne genaue Bilanz.

Die Tipps liegen in `swiss.json` unter `qualifierPredictions` und werden nicht den einzelnen Matches zugeordnet. Beispielstruktur für eine Person:

```json
{
  "threeZero": "GEN",
  "threeOne": "G2",
  "threeTwo": "BLG",
  "additional": ["T1", "HLE", "TLAW", "DK", "AL"]
}
```

**Dieses Beispiel stammt nur aus der als Layoutvorlage gesendeten Abbildung und ist in der Live-Datei noch keiner Person zugeordnet.** Alle echten Tipps sind bis zur Mitteilung `null` beziehungsweise `[]`.

Als `team`-Codes müssen die bekannten Bezeichner verwendet werden. Acht Teams pro Person dürfen sich nicht wiederholen.

Der separat dargestellte Spielplan verwendet `matches[]` derselben Datei, mit UTC-Anstoßzeiten (`startUtc`), der angesetzten Runde und `teamA` / `teamB` aus den offiziellen Begegnungen. Die Oberfläche wandelt Uhrzeiten automatisch nach `Europe/Berlin` um. Gegner späterer Runden werden nach der Auslosung nachgetragen. Match-Ergebnisse und individuelle Matchtipps gehören nicht zur Swiss-Vorhersage.

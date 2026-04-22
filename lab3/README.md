# **Labor 3** - Kommunikation über Nachrichten mit ZeroMQ

Im dritten Labor untersuchen wir eine konkrete Technik der
*Nachrichtenkommunikation*. Dabei werden zunächst drei Beispiele der wichtigsten
Kommunikationsmuster mit dem [ZeroMQ Framework](http://zeromq.org) (0MQ)
betrachtet. Eines davon, das *Paralel Pipeline* Muster, bildet in der Folge die
Grundlage der Programmieraufgabe. Dabei wird ein einfaches System für die
verteilte Datenverarbeitung realisiert, das dem Grundprinzip von MapReduce
Algorithmen aus der bekannten [Hadoop
Plattform](https://de.wikipedia.org/wiki/Apache_Hadoop) entspricht.

Allgemeine **Ziele** dieses Labors:

- Untersuchung höherwertiger Dienste zur Nachrichtenkommunikation
- Kennenlernen verschiedener Kommunikationsmuster
- Anwendung des verbreiteten ZeroMQ Frameworks
- Veranschaulichung von Konzepten der Massendatenverarbeitung

## 1. Vorbereitung

### 1.1. Software installieren

Für diese Aufgabe werden keine neuen Installationen benötigt.

### 1.2. Projekt aktualisieren

Aktualisieren Sie die Kopie des VS2Lab Repositories auf Ihrem Arbeitsrechner (alle Beispiele für Linux/Mac):

```bash
cd ~/git/vs2lab # angenommen hier liegt das vs2lab Repo
git add . # ggf. eigene Änderungen vormerken
git commit -m 'update' # ggf eigene Änderungen per Commit festschreiben
git checkout master # branch auswählen (falls nicht schon aktiv)
git pull # aktualisieren
```

### 1.3. Python Umgebung installieren

Hier hat sich nichts geändert. Ggf. aktualisieren wie folgt:

```bash
cd ~/git/vs2lab # angenommen hier liegt das vs2lab Repo
pipenv update
```

### 1.4. Beispielcode für diese Aufgabe

Wechseln Sie auf Ihrem Arbeitsrechner in das Unterverzeichnis dieser Aufgabe:

```bash
cd ~/git/vs2lab # angenommen hier liegt das vs2lab Repo
cd lab3
```

## 2. Beispiele: einfache und erweiterte Kommunikationsmuster

Das Labor beginnt mit einigen Beispielen zum Messaging mit 0MQ. Die Beispiele
zeigen die drei gängigsten 0MQ-Muster.

Allgemeine Beschreibungen der Muster und der dazugehörigen 0MQ Sockets finden
sich z.B. hier:

- [Request-Reply: Ask and Ye Shall
  Receive](https://zguide.zeromq.org/docs/chapter1/#Ask-and-Ye-Shall-Receive)
- [Publish-Subscribe: Getting the Message
  Out](https://zguide.zeromq.org/docs/chapter1/#Getting-the-Message-Out)
- [Parallel Pipeline: Divide and
  Conquer](https://zguide.zeromq.org/docs/chapter1/#Divide-and-Conquer)

### 2.1. Request-Reply

Das erste Beispiel zeigt, wie die gängige Request-Reply Kommunikation mit 0MQ
*Request-* und *Reply-Sockets* gegenüber den einfachen Berkeley Sockets
vereinfacht werden kann. 0MQ verwendet dabei Nachrichten statt Streams und es
wird keine Angabe der Übertragungsgröße benötigt. Ein Request Socket des Client
wird jeweils mit einem Reply Socket des Server gekoppelt.

Sie starten Server und Client nach dem nun schon bekannten Muster in zwei
Terminals.

#### Terminal1

```bash
cd ~/git/vs2lab/lab3/zmq1 # angenommen hier liegt das vs2lab Repo
pipenv run python server.py
```

#### Terminal2

```bash
cd ~/git/vs2lab/lab3/zmq1 # angenommen hier liegt das vs2lab Repo
pipenv run python client.py
```

Wir wollen nun noch etwas experimentieren. Zunächst schauen wir uns an, was es
bedeutet, dass 0MQ asynchron arbeitet. Probieren Sie dazu folgende Kombination
aus:

1. Terminal1: `pipenv run python client.py`
2. Terminal2: `pipenv run python server.py`

Die Kopplung von je zwei Sockets können Sie durch folgendes erweiterte
Experiment nachverfolgen:

1. Terminal1: `pipenv run python client.py`
2. Terminal2: `pipenv run python client1.py`
3. Terminal3: `pipenv run python server.py`

**Aufgabe Lab3.1:** Erklären Sie das Verhalten der Systeme in den beiden
Experimenten.

### 2.2. Publish-Subscribe

Mit dem Publish-Subscribe Muster lässt sich *1-n Kommunikation* (ein Sender, n
Empfänger) realisieren. Zudem können Nachrichten nach Themen gefiltert werden.

Wechseln Sie zunächst in das entsprechende Verzeichnis:

```bash
cd ~/git/vs2lab/lab3/zmq2 # angenommen hier liegt das vs2lab Repo
```

#### Experiment1

1. Terminal1: `pipenv run python server.py`
2. Terminal2: `pipenv run python client.py`
3. Terminal3: `pipenv run python client.py`

1. Terminal1: -

2. Terminal2: `pipenv run python client.py`
b'TIME 14:45:29.475809'
b'TIME 14:45:34.489311'
b'TIME 14:45:39.489882'
b'TIME 14:45:42.438560'
b'TIME 14:45:47.455641'

3. Terminal3: `pipenv run python client.py`
b'TIME 14:45:42.438560'
b'TIME 14:45:47.455641'
b'TIME 14:45:52.458419'
b'TIME 14:45:57.462452'
b'TIME 14:46:02.466176'

Erklärung: Jeder Client sieht nur Nachrichten ab dem Zeitpunkt, an dem er verbunden ist und sein Subscribe aktiv ist. Deshalb sieht Terminal3 erst spätere Nachrichten, obwohl der Server von Anfang an sendet (keine Nachlieferung alter Messages).

#### Experiment 2

1. Terminal1: `pipenv run python server.py`
2. Terminal2: `pipenv run python client.py`
3. Terminal3: `pipenv run python client1.py`

1. Terminal1: `pipenv run python server.py`
-
2. Terminal2: `pipenv run python client.py`
b'TIME 14:47:17.893259'
b'TIME 14:47:22.894005'
b'TIME 14:47:27.901577'
b'TIME 14:47:32.920286'
b'TIME 14:47:35.860837'
3. Terminal3: `pipenv run python client1.py`
b'DATE 2026-04-20'
b'DATE 2026-04-20'
b'DATE 2026-04-20'

Erklärung: Clients filtern nach Topics: client abonniert offenbar TIME und client1 DATE. Daher bekommt Terminal2 nur TIME ... und Terminal3 nur DATE, obwohl beide vom selben Publisher kommen. 

**Aufgabe Lab3.2:** Erklären Sie das Verhalten der Systeme in den beiden
Experimenten.

### 2.3. Parallel Pipeline

Das letzte Beispiel zeigt die Verteilung von Nachrichten von mehreren Sendern
auf mehrere Empfänger. Sogenannte 'Farmer' (`tasksrc.py`) erstellen Aufgaben
('Tasks') die von einer Menge von 'Workern' (`taskwork.py`) verarbeitet werden.
Die Tasks eines Farmers können an jeden Worker gehen und Worker akzeptieren
Tasks von jedem Farmer. Bei mehreren Alternativen Farmer/Worker Prozessen werden
die Tasks gleichverteilt.

`tasksrc.py` wird mit der Farmer-ID (1 oder 2) als Parameter gestartet. Jede
Farmer-ID darf nur einmal verwendet werden, da sie einen *PUSH-Socket* bindet.

`taskwork.py` wird mit der Worker-ID (beliebig) als Parameter gestartet. Die
Worker-ID dient nur der Anzeige. Es können beliebig viele Worker gestartet
werden, die jeweils mit ihrem *PULL-Sockets* die beiden Farmer kontaktieren.

Wechseln Sie zunächst in das entsprechende Verzeichnis:

```bash
cd ~/git/vs2lab/lab3/zmq3 # angenommen hier liegt das vs2lab Repo
```

Gehen sie nun wie folgt vor:

#### Experiment1

Grundsätzlich: Farmer(tasksrc.py) erzeugen Tasks und schicken sie per Push. Worker(taskwork.py) holen sie per Pull, Tasks per round-robin auf verfügbaren Worker.

1. Terminal1: `pipenv run python tasksrc.py 1`
2. Terminal2: `pipenv run python tasksrc.py 2`
3. Terminal3: `pipenv run python taskwork.py 1`

1. Terminal1: `pipenv run python tasksrc.py 1`
-
2. Terminal2: `pipenv run python tasksrc.py 2`
-
3. Terminal3: `pipenv run python taskwork.py 1`
1 started
1 received workload 2 from 1
1 received workload 6 from 2
1 received workload 58 from 1
1 received workload 79 from 2
1 received workload 39 from 1
1 received workload 65 from 2
...
1 received workload 26 from 1
1 received workload 15 from 2
1 received workload 24 from 1
1 received workload 85 from 2
1 received workload 57 from 1
1 received workload 90 from 2
1 received workload 70 from 1
1 received workload 45 from 2

Erklärung: Ein Worker bekommt Tasks abwechselnd von Farmer 1 und 2 (100 je Farmer, 1 Worker muss alle abarbeiten) -> langsam

#### Experiment 2

1. Terminal1: `pipenv run python taskwork.py 1`
2. Terminal2: `pipenv run python taskwork.py 2`
3. Terminal3: `pipenv run python tasksrc.py 1`

1. Terminal1: `pipenv run python taskwork.py 1`
1 started
1 received workload 16 from 1
1 received workload 25 from 1
1 received workload 1 from 1
1 received workload 54 from 1
1 received workload 68 from 1
1 received workload 11 from 1
1 received workload 41 from 1
1 received workload 12 from 1
...
1 received workload 65 from 1
1 received workload 19 from 1
1 received workload 83 from 1
1 received workload 6 from 1
1 received workload 47 from 1
2. Terminal2: `pipenv run python taskwork.py 2`
2 started
2 received workload 18 from 1
2 received workload 64 from 1
2 received workload 66 from 1
2 received workload 3 from 1
2 received workload 28 from 1
2 received workload 95 from 1
...
2 received workload 6 from 1
2 received workload 70 from 1
2 received workload 49 from 1
2 received workload 89 from 1
2 received workload 69 from 1
2 received workload 59 from 1
3. Terminal3: `pipenv run python tasksrc.py 1`
-

Erklärung: Tasks auf Worker 1 und Worker 2 verteilt, jeder sieht nur ein Teil der Tasks. (100 Tasks werde auf 2 Worker verteilt also jeweils 50) schneller da mehr Parallelität, weniger Tasks je Worker.  

**Aufgabe Lab3.3:** Erklären Sie das Verhalten der Systeme in den beiden
Experimenten.

## 3 Aufgabe

In der Programmieraufgabe soll das Parallel Pipeline Muster verwendet werden, um
die verteilte Verarbeitung von Textdaten zu realisieren.

## 3.1 Übersicht

Wir wollen das berühmte **Wordcount** Beispiel für *Hadoop MapReduce* mit 0MQ
nachprogrammieren (näherungsweise). Das Prinzip ist wie folgt:

- Das verteilte System besteht aus einem zentralen 'Split'-Prozess ('Splitter'),
  einer variablem Menge von 'Map'-Prozessen ('Mapper') und einer festen Menge
  von 'Reduce'-Prozessen ('Reducer').
- Der Splitter lädt aus einer Datei zeilenweise Sätze aus und verteilt sie als
  Nachrichten gleichmäßig an die die Mapper.
- Ein Mapper nimmt jeweils Sätze entgegen. Jeder Satz wird dann zunächst in
  seine Wörter zerlegt. Schließlich ordnet der Mapper jedes Wort nach einem
  festen Schema genau einem der Reducer zu und sendet es als Nachricht an
  diesen.
- Ein Reducer sammelt die an ihn geschickten Wörter ein und zählt sie. Beachten
  sie: durch das feste zuordnungsschema kommen alle gleichen Wörter beim selben
  Reducer an und dieser Zählt 'seine' Wörter also garantiert komplett. Das
  Gesamtergebnis ergibt sich aus der Vereinigung der Teilergebnisse aller
  Reducer.

## 3.2 Aufgabe und Anforderungen kurz und knapp

Sie sollen die oben beschriebenen Prozesse als Python Skripte implementieren und
die Kommunikation zwischen diesen mit dem 0MQ Parallel Pipeline Muster
realisieren. Verwenden Sie:

- einen Splitter
- drei Mapper
- zwei Reducer

Der Splitter kann entweder eine Datei lesen oder die Sätze zufällig generieren.
Der Reducer soll bei jeder Aktualisierung den aktuellen Zähler des neuen Wortes
ausgeben.

### 3.3 Tipps

Neben dem dritten Beispiel liefert die Beschreibung in

- [Parallel Pipeline: Divide and
  Conquer](https://zguide.zeromq.org/docs/chapter1/#Divide-and-Conquer)

ein nützliches Beispiel, an dem Sie sich orientieren können.

... stay tuned (Hinweise zur Installation/Konfiguration im Labor-README)

### 3.4 Abgabe

Die Abgabe erfolgt durch Abnahme durch einen Dozenten. Packen Sie den kompletten
Code zudem als Zip Archiv und laden Sie dieses im ILIAS hoch.

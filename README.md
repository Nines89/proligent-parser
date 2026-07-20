# Proligent Parser

Applicazione per interrogare **Proligent Analytics** (report di produzione/test), scaricare i dati in tabella e analizzarli tramite interfaccia grafica o riga di comando.

Il programma si connette al portale aziendale Proligent, effettua il login con le credenziali Microsoft aziendali e recupera i report come `pandas DataFrame`, con supporto per filtri, paginazione automatica, shortcut salvati, export CSV, dashboard e download documenti.

---

## Indice

1. [Requisiti](#requisiti)
2. [Accesso e registrazione](#accesso-e-registrazione)
3. [Installazione](#installazione)
4. [Avvio del programma](#avvio-del-programma)
5. [Launcher (`launch.vbs`)](#launcher-launchvbs)
6. [Login](#login)
7. [Shortcut UUID](#shortcut-uuid)
8. [Interfaccia grafica (GUI)](#interfaccia-grafica-gui)
9. [Riga di comando (CLI)](#riga-di-comando-cli)
10. [Uso come libreria Python](#uso-come-libreria-python)
11. [Struttura del progetto](#struttura-del-progetto)
12. [Risoluzione problemi](#risoluzione-problemi)

---

## Requisiti

### Software

| Componente | Versione minima | Note |
|---|---|---|
| **Python** | 3.10+ | Consigliato 3.11 o superiore |
| **Microsoft Edge** | Qualsiasi versione recente | Obbligatorio: il login usa Edge tramite Playwright |
| **Rete aziendale** | VPN / intranet | Accesso al server Proligent (vedi sotto) |

### Dipendenze Python

Le dipendenze sono elencate in `requirements.txt`:

- `requests` — chiamate API HTTP autenticate
- `playwright` — automazione browser per login e paginazione Discovery
- `pandas` — gestione dati tabellari
- `beautifulsoup4`, `lxml` — parsing HTML dei report SSRS
- `PySide6` — interfaccia grafica
- `rich` — output formattato da riga di comando

### Server Proligent

Il client si connette di default a:

```
https://us70uwapp136.zam.alcatel-lucent.com:6443/Analytics
```

È necessario essere raggiungibili da rete aziendale (VPN o rete locale Nokia/Alcatel-Lucent).

---

## Accesso e registrazione

### Chi può usare il programma

Per utilizzare Proligent Parser serve un account **Microsoft aziendale** (Azure AD / Entra ID) con accesso autorizzato al portale **Proligent Analytics**.

### Dove registrarsi

1. **Account Microsoft aziendale** — gestito dall'IT aziendale (Nokia / Alcatel-Lucent). Se non si dispone di credenziali, richiederle al reparto IT o al referente del sito produttivo.
2. **Accesso a Proligent Analytics** — l'utente deve essere abilitato sul portale Proligent del proprio sito. In caso di errore di autorizzazione dopo il login, contattare l'amministratore Proligent del reparto.

### Verifica accesso manuale

Prima di usare il parser, verificare di poter accedere al portale dal browser:

1. Aprire Edge e navigare a:
   `https://us70uwapp136.zam.alcatel-lucent.com:6443/Analytics/Home/Home`
2. Completare il login Microsoft (email aziendale + password).
3. Se richiesto, completare la **MFA** (autenticazione a più fattori).
4. Confermare che la home Proligent Analytics si carichi correttamente.

Se il login manuale funziona, anche il parser potrà autenticarsi (eventualmente con MFA interattiva al primo accesso).

---

## Installazione

### 1. Clonare o copiare il progetto

```powershell
cd C:\<percorso>\proligent-parser
```

### 2. Creare un ambiente virtuale (consigliato)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Su Windows, se il comando `python` non è riconosciuto, usare sempre `py -3` al suo posto.

### 3. Installare le dipendenze

```powershell
pip install -r requirements.txt
```

### 4. Installare i browser Playwright

Playwright usa il canale **msedge** (Microsoft Edge già installato sul sistema). Installare i componenti Playwright:

```powershell
playwright install
```

> **Nota:** Edge deve essere già presente su Windows. Il programma lo individua automaticamente in `Program Files` o `LocalAppData`.

### 5. Creare il file degli shortcut (obbligatorio al primo avvio)

Il repository **non** include `saved_shortcuts.json` (è personale e ignorato da Git). Devi crearlo tu una sola volta, partendo dall'esempio:

1. Nella cartella del progetto, trova il file `saved_shortcuts.example.json`.
2. Copialo e rinomina la copia in `saved_shortcuts.json`:

```powershell
Copy-Item saved_shortcuts.example.json saved_shortcuts.json
```

3. (Opzionale) Apri `saved_shortcuts.json` con un editor di testo e sostituisci gli UUID/nomi di esempio con i tuoi shortcut Proligent.
4. Salva il file. Da questo momento la GUI userà e aggiornerà automaticamente `saved_shortcuts.json`.

> **Importante:** non modificare né committare `saved_shortcuts.example.json` con i tuoi dati reali. Quello resta solo come modello per gli altri utenti. I tuoi shortcut vanno solo in `saved_shortcuts.json`.

---

## Avvio del programma

### Metodo consigliato: doppio click su `launch.vbs`

Per l'uso quotidiano, il modo più semplice è avviare il programma tramite il **launcher** incluso nel progetto:

1. Aprire la cartella `proligent-parser`
2. Fare **doppio click** su `launch.vbs`

Si apre la GUI senza mostrare finestre di terminale in background.

> Per creare un collegamento sul Desktop: tasto destro su `launch.vbs` → **Invia a** → **Desktop (crea collegamento)**. Opzionalmente rinominare il collegamento in "Proligent Parser".

### Avvio manuale da terminale

```powershell
# Interfaccia grafica
python gui.py

# Riga di comando
python main.py

# Batch launcher (mostra eventuali errori in console)
avvia_proligent_parser.bat
```

---

## Launcher (`launch.vbs`)

Il launcher è la catena di avvio pensata per gli utenti finali su Windows. Consente di aprire l'applicazione con un doppio click, senza aprire una finestra CMD visibile, e registra automaticamente un log di ogni sessione.

### Come funziona

```
launch.vbs  →  avvia_proligent_parser.bat  →  python gui.py
   (VBS)              (batch)                    (GUI)
```

| File | Ruolo |
|---|---|
| **`launch.vbs`** | Script VBScript che invoca il batch in modo **nascosto** (nessuna finestra nera di prompt) |
| **`avvia_proligent_parser.bat`** | Trova Python sul sistema, avvia `gui.py` e scrive il log in `logs/` |
| **`gui.py`** | Interfaccia grafica del programma |

### `launch.vbs`

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "avvia_proligent_parser.bat", 0, False
```

- Il secondo parametro `0` indica esecuzione **invisibile** (nessuna finestra console).
- Il terzo parametro `False` indica che lo script VBS **non attende** la chiusura della GUI (l'applicazione resta aperta in modo indipendente).

### `avvia_proligent_parser.bat`

Il batch esegue in sequenza:

1. Si posiziona nella cartella del progetto (`cd /d "%~dp0"`)
2. Crea la cartella `logs/` se non esiste
3. **Rileva Python** nell'ordine:
   - `.venv\Scripts\python.exe` (se il venv esiste nella cartella del progetto)
   - `py -3` (Python Launcher for Windows)
   - `python`
   - `pythonw`
4. Avvia `gui.py` reindirizzando stdout e stderr nel file di log
5. Registra il codice di uscita al termine della sessione

Se Python non è installato o non è nel `PATH`, il batch termina con errore e lo registra nel log.

### File di log

Ogni avvio produce un file in `logs/` con nome:

```
launcher_AAAAMMGG.log
```

Esempio: `launcher_20260713.log` per il 13 luglio 2026.

Il log contiene:

- Data/ora di avvio e chiusura
- Comando Python utilizzato (`py -3`, `python`, ecc.)
- Tutti i messaggi `[proligent] ...` (login, query, paginazione)
- Eventuali errori o warning Python/Qt
- **Exit code** finale (`0` = chiusura normale)

Utile per diagnosticare problemi quando la GUI si chiude inaspettatamente o una query fallisce senza messaggi evidenti.

### Requisiti del launcher

- **Windows** con supporto VBScript (`wscript.exe`, presente di default)
- **Python** installato e raggiungibile da `py`, `python` o `pythonw`
- Dipendenze già installate nel venv (`pip install -r requirements.txt` con `.venv` attivo) oppure nel Python di sistema
- Se è presente la cartella `.venv`, il launcher la usa automaticamente
- I file `launch.vbs` e `avvia_proligent_parser.bat` devono restare **nella stessa cartella** del progetto

### Collegamento sul Desktop o nella barra delle applicazioni

1. Tasto destro su `launch.vbs` → **Invia a** → **Desktop (crea collegamento)**
2. (Opzionale) Tasto destro sul collegamento → **Proprietà** → cambiare l'icona
3. Trascinare il collegamento sulla barra delle applicazioni per un accesso rapido

> **Nota:** il collegamento deve puntare a `launch.vbs`, non direttamente a `gui.py`. In questo modo l'avvio resta silenzioso e viene scritto il log.

### Differenza tra i metodi di avvio

| Metodo | Finestra CMD | Log automatico | Uso consigliato |
|---|---|---|---|
| `launch.vbs` | No | Sì | Uso quotidiano, utenti finali |
| `avvia_proligent_parser.bat` | Sì (breve) | Sì | Debug avvio / Python non trovato |
| `python gui.py` | Sì | No | Sviluppo, messaggi in tempo reale |
| `python main.py` | Sì | No | Query da riga di comando |

---

## Login

Il login avviene tramite **Microsoft Edge** con un profilo browser dedicato salvato nella cartella `.proligent-browser-data/`. Dopo il primo accesso riuscito, i cookie di sessione vengono conservati e i login successivi sono più rapidi.

### Login dalla GUI

1. Avviare `gui.py`.
2. Cliccare **Login Proligent**.
3. Il browser si apre in modalità headless (invisibile): il programma tenta il login automatico usando il profilo salvato.
4. Se è la prima volta o la sessione è scaduta:
   - Se le credenziali non sono nel profilo, potrebbe essere necessario completare MFA o il login manualmente (in quel caso usare la CLI con username/password, oppure effettuare un login interattivo — vedi sotto).
5. Al termine, lo stato passa da **Non connesso** a **Connesso** (verde) e i pulsanti **Carica** (shortcut) e **Esegui Query** vengono abilitati.

### Login da riga di comando

```powershell
# Login interattivo (chiede la password)
python main.py --username nome.cognome@azienda.com

# Login con password esplicita
python main.py --username nome.cognome@azienda.com --password "..." --headless

# Solo login + lista report disponibili
python main.py --username nome.cognome@azienda.com --list-reports
```

| Opzione | Descrizione |
|---|---|
| `--username`, `-u` | Email aziendale Microsoft |
| `--password`, `-p` | Password (se omessa, viene richiesta in modo sicuro) |
| `--headless` | Browser invisibile durante il login |

### MFA (autenticazione a più fattori)

Se l'account richiede MFA:

- **Senza credenziali in CLI:** il programma apre il browser e attende fino a 3 minuti che l'utente completi MFA manualmente.
- **Con credenziali in CLI:** username e password vengono inseriti automaticamente; l'utente deve comunque completare MFA nel browser se richiesto.

### Profilo browser persistente

La cartella `.proligent-browser-data/` contiene:

- Cookie di sessione Proligent / Microsoft
- Preferenze Edge del profilo dedicato

**Non condividere** questa cartella: contiene dati di sessione personali.

Per forzare un nuovo login, eliminare la cartella `.proligent-browser-data/` e riavviare il programma.

---

## Shortcut UUID

Gli **shortcut** sono report personalizzati salvati su Proligent Analytics. Ogni shortcut ha un identificativo **UUID** (es. `f703ee44-8653-24e0-9956-c8f4f4810a12`) che il parser usa per caricare direttamente i dati pre-filtrati.

### Come creare shortcut su Proligent

Dopo aver creato la tabella con i filtri desiderati premenre il tasto **Actions** e poi **Create**, compilare i campi e salvare la selezione.

### Come trovare l'UUID di uno shortcut su Proligent

1. Accedere a Proligent Analytics dal browser.
2. Aprire la sezione **Report** e poi, nel menù a tendina che si viene a creare una sezione **Reports Shortcuts**. Clicca sul singolo shortcut per visualizzarlo.
3. Nell'URL del browser comparirà un parametro `id=` seguito dall'UUID:

   ```
   https://.../Analytics/Discovery?id=f703ee44-8653-24e0-9956-c8f4f4810a12&viewmode=table
   ```

4. Copiare la stringa UUID (formato `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).


### Usare gli shortcut nella GUI

1. Dopo il login, andare al campo **Shortcut:**.
2. Incollare l'UUID nel campo oppure selezionare uno shortcut già salvato dal menu a tendina.
3. Cliccare **Carica**.
4. Il programma apre la pagina Discovery in background, scorre tutte le pagine del report SSRS e carica i dati nella griglia, tab **Dati**.

### Configurare il file degli shortcut (cosa deve fare l'utente)

Due file diversi — non confonderli:

| File | Ruolo | Cosa fare |
|---|---|---|
| `saved_shortcuts.example.json` | Modello di esempio **nel repository** | Solo da leggere / copiare. Non inserire qui i tuoi UUID reali. |
| `saved_shortcuts.json` | Elenco **locale** dei tuoi shortcut | Devi crearlo tu (copia dall'esempio). Qui salvi i tuoi UUID. Non viene committato in Git. |

**Cosa fare al primo utilizzo**

1. Se non hai ancora `saved_shortcuts.json`, crealo come descritto in [Installazione §5](#5-creare-il-file-degli-shortcut-obbligatorio-al-primo-avvio):
   ```powershell
   Copy-Item saved_shortcuts.example.json saved_shortcuts.json
   ```
2. Apri `saved_shortcuts.json` e sostituisci gli esempi con i tuoi UUID Proligent (oppure lascia il file vuoto `[]` e aggiungi tutto dalla GUI).
3. Avvia il programma: nel menu a tendina **Shortcut** vedrai gli elementi presenti nel file.

**Cosa fare nell'uso quotidiano (dalla GUI)**

| Azione | Come |
|---|---|
| **Salvare** | Inserire UUID + nome opzionale nel campo "Nome per questo shortcut", poi **Salva** |
| **Aggiornare** | Selezionare uno shortcut esistente, modificare il nome, **Salva** |
| **Eliminare** | Selezionare lo shortcut dall'elenco e cliccare **Elimina** |

Ogni salvataggio/eliminazione dalla GUI aggiorna automaticamente `saved_shortcuts.json` sul tuo PC. Non serve toccare Git.

Formato atteso del file:

```json
[
  {
    "uuid": "f703ee44-8653-24e0-9956-c8f4f4810a12",
    "label": "UFAN10 - JABIL_001"
  }
]
```

### Paginazione automatica degli shortcut

Gli shortcut con molte pagine di risultati vengono scaricati automaticamente: il client naviga ogni pagina della vista Discovery (modalità tabella) e concatena tutti i record in un unico dataset.

---

## Interfaccia grafica (GUI)

### Panoramica

```
┌─────────────────────────────────────────────────────────┐
│  [Login Proligent]   Stato: Connesso                    │
├─────────────────────────────────────────────────────────┤
│  Tab: Shortcut UUID                                     │
│  [UUID ▼]  [Carica]   Nome: [____] [Salva] [Elimina]   │
├─────────────────────────────────────────────────────────┤
│  Da: [date]  A: [date]  [Filtra date] [Tutte]          │
│  [Ultime 24h] [Ultima settimana] [Ultimo mese]         │
├─────────────────────────────────────────────────────────┤
│  [Rimuovi filtri griglia]              [Esporta CSV]    │
├─────────────────────────────────────────────────────────┤
│  Tab risultati:  [ Dati ]  [ Dashboard ]                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Griglia dati (ordinabile, filtrabile)            │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Campo Shortcut UUID

È il metodo principale per caricare dati: si incolla o si seleziona l'UUID di uno shortcut Proligent e si clicca **Carica**.

### Filtri per data (barra superiore)

Dopo aver caricato i dati, è possibile restringere il periodo **sui dati già in memoria**:

| Controllo | Funzione |
|---|---|
| **Da / A** | Selettori data con calendario |
| **Filtra date** | Applica il filtro sul campo *Start Time* |
| **Tutte** | Rimuove il filtro data e ripristina tutti i record caricati |
| **Ultime 24h** | Ultimo giorno |
| **Ultima settimana** | Ultimi 7 giorni |
| **Ultimo mese** | Ultimi 30 giorni |

### Griglia dati (tab **Dati**)

| Funzione | Come usarla |
|---|---|
| **Ordinamento** | Clic sull'intestazione di colonna |
| **Filtro stile Excel** | Clic sull'intestazione → dialog con valori univoci, ricerca, seleziona/deseleziona tutto |
| **Filtro rapido** | Click destro su una cella → *Mostra solo* / *Escludi* |
| **Copia** | Click destro → *Copia cella* o *Copia riga* |
| **Rimuovi filtri griglia** | Pulsante in toolbar |
| **Contatore righe** | Barra di stato: mostra righe visibili e serial number unici |

#### Colori status

| Status | Colore sfondo |
|---|---|
| **Pass** | Verde |
| **Fail** | Rosso |
| **Aborted** | Giallo |

#### Download documenti

Se la colonna **Documents** contiene un valore (non `0`), il testo appare come link blu sottolineato:

- **Click sinistro** sulla cella Documents → scarica lo ZIP dei documenti associati al test.
- **Click destro** → *Scarica documenti*.

#### Unit Results View

Per le righe con dati disponibili, dal menu contestuale (click destro) è possibile scegliere **Apri Unit Results View**: si apre una finestra Edge con la vista dettaglio dell'unità su Proligent.

### Tab Dashboard

Mostra un riepilogo analitico dei dati **attualmente filtrati** nella griglia:

- **KPI:** record totali, serial number, prodotti, yield (% Pass), Fail
- **Grafici:**
  - Distribuzione esiti (torta)
  - Test per prodotto (barre)
  - Yield per prodotto (%)
  - Tempo medio di test per prodotto
  - Test nel tempo (per giorno, ultimi 30 giorni)

### Export CSV

1. Applicare eventuali filtri desiderati.
2. Cliccare **Esporta CSV**.
3. Scegliere il percorso di salvataggio.

Vengono esportate **solo le righe visibili** (rispettando filtri griglia e data). Encoding: UTF-8 con BOM (`utf-8-sig`), compatibile con Excel.

---

## Uso come libreria Python

```python
from proligent_client import ProligentClient

client = ProligentClient()
client.login(username="user@azienda.com", password="...", headless=True)

# Query con filtri
df = client.query(
    "OperationRuns",
    station="FST_JB_PRO_001",
    date_from="2026-06-01",
    date_to="2026-06-30",
    status="Pass",
)

# Query tramite shortcut UUID
df = client.query("f703ee44-8653-24e0-9956-c8f4f4810a12")

# Elenco report
reports = client.get_available_reports()

# Configurazione report
config = client.get_report_config("OperationRuns")

print(df)
```

---

## Struttura del progetto

```
proligent-parser/
├── launch.vbs                 # Launcher principale (doppio click, avvio silenzioso)
├── avvia_proligent_parser.bat # Script batch: trova Python, avvia GUI, scrive log
├── proligent_client.py        # Client API: login, query, paginazione, download
├── gui.py                     # Interfaccia grafica PySide6
├── main.py                    # Entry point riga di comando
├── requirements.txt           # Dipendenze Python
├── saved_shortcuts.example.json  # Esempio di shortcut UUID (committato)
├── saved_shortcuts.json          # Shortcut locali dell'utente (gitignored)
├── .proligent-browser-data/       # Profilo Edge (sessione, cookie) — generato
├── .proligent-browser-data-viewer/  # Profilo Edge per Unit Results View
└── logs/                      # Log giornalieri del launcher (launcher_AAAAMMGG.log)
```

---

## Risoluzione problemi

### Doppio click su `launch.vbs` ma non succede nulla

1. Aprire `avvia_proligent_parser.bat` direttamente (doppio click): se compare un errore, leggere il messaggio in console.
2. Controllare l'ultimo file in `logs/launcher_*.log` per errori Python o dipendenze mancanti.
3. Verificare che Python sia installato: aprire un terminale e digitare `py -3 --version` o `python --version`.
4. Se Windows blocca lo script, tasto destro su `launch.vbs` → **Proprietà** → eventuale spunta **Sblocca**.

### Python non trovato (nel log: `Python NON trovato`)

Installare Python da [python.org](https://www.python.org/downloads/) o dal software center aziendale, assicurandosi di selezionare **"Add Python to PATH"** durante l'installazione. In alternativa installare il [Python Launcher](https://docs.python.org/3/using/windows.html#python-launcher-for-windows) (`py`).

### "Login non completato" / timeout MFA

- Verificare la connessione VPN.
- Riprovare senza `--headless` per vedere il browser e completare MFA manualmente.
- Eliminare `.proligent-browser-data/` e rifare il login.

### "Esegui client.login() prima di fare query"

Effettuare il login prima di qualsiasi operazione (pulsante **Login Proligent** in GUI o `client.login()` in codice).

### Nessun dato trovato

- Verificare che lo shortcut UUID sia corretto e che lo shortcut contenga dati nel periodo configurato su Proligent.
- Controllare i filtri data applicati nella GUI.
- Provare ad aprire lo stesso shortcut direttamente nel browser Proligent.

### Edge non trovato

Installare Microsoft Edge su Windows. Il programma cerca l'eseguibile in:

- `%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe`
- `%ProgramFiles%\Microsoft\Edge\Application\msedge.exe`
- `%LocalAppData%\Microsoft\Edge\Application\msedge.exe`

### Errore certificato SSL / HTTPS

Il client disabilita la verifica SSL (`verify=False`) perché il server Proligent usa un certificato interno. Questo è intenzionale per l'ambiente aziendale.

### Query lenta su shortcut grandi

Gli shortcut con molte pagine richiedono la navigazione automatica di ogni pagina Discovery. L'overlay nella GUI mostra l'avanzamento (*Raccolta pagina X di Y…*). Attendere il completamento.

### Manca `saved_shortcuts.json` / shortcut non compaiono nel menu

Il file non è incluso nel repository: ogni utente deve crearlo in locale.

1. Nella cartella del progetto esegui:
   ```powershell
   Copy-Item saved_shortcuts.example.json saved_shortcuts.json
   ```
2. Se preferisci partire da zero, crea invece un file `saved_shortcuts.json` con contenuto `[]`.
3. Riavvia la GUI: gli shortcut (se presenti nel file) appariranno nel menu a tendina.
4. Se il file esiste ma non si aggiorna, verifica i permessi di scrittura sulla cartella del progetto.

---

## Note legali e sicurezza

- Le credenziali **non** vengono salvate nel codice sorgente.
- I cookie di sessione restano nel profilo locale `.proligent-browser-data/`.
- Non condividere il profilo browser né il file `saved_shortcuts.json` se contengono dati sensibili di produzione.
- L'uso del tool è soggetto alle policy IT aziendali e ai termini di utilizzo di Proligent Analytics.

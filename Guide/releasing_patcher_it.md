## Creare una release del patcher

Il repository include il workflow GitHub Actions `.github/workflows/build-gui.yml`, che genera automaticamente:

- un eseguibile autonomo per Windows;
- un'AppImage per Linux;
- un'applicazione macOS in formato ZIP.

### 1. Aggiorna la versione

Modifica `PATCHER_VERSION` in `Database/GUI_Patcher/GUI/patcher_gui.py`. La versione italiana usa il formato `1.2.1-it.1`, che indica sia la base tecnica inglese sia la revisione della localizzazione.

### 2. Verifica e pubblica le modifiche

Esegui almeno il controllo sintattico:

```bash
python -m py_compile Database/GUI_Patcher/GUI/patcher_gui.py Database/GUI_Patcher/GUI/gui_backend.py Database/GUI_Patcher/GUI/randomizer/pro_randomizer.py
```

Poi crea un commit e pubblicalo sul branch principale.

Se, come nel lavoro corrente, hai rimosso localmente un commit che era già presente su `origin/master`, il normale push verrà rifiutato perché la cronologia remota è più avanti. Dopo avere verificato che nessun collaboratore abbia pubblicato altri commit nel frattempo, aggiorna il branch remoto con:

```bash
git push --force-with-lease origin master
```

Usa `--force-with-lease`, non `--force`: il comando interrompe l'operazione se il branch remoto è cambiato senza che tu lo sappia. Se non vuoi riscrivere la cronologia pubblica, recupera invece il commit remoto e annullalo con un nuovo commit di revert.

### 3. Crea e pubblica il tag

Il tag deve iniziare con `gui-v` e corrispondere alla versione del programma:

```bash
git tag -a gui-v1.2.1-it.1 -m "Patcher italiano v1.2.1-it.1"
git push origin gui-v1.2.1-it.1
```

Il push del tag avvia il workflow **Build GUI Patcher**. Al termine, il job `publish-release` crea automaticamente la release GitHub e allega i tre pacchetti.

### 4. Completa la pagina della release

Apri la sezione [Releases](https://github.com/Lurpigi/DQMJ2Pro_Translation/releases), modifica la release generata e aggiungi:

- una breve descrizione della versione;
- le novità e i problemi risolti;
- l'avvertenza di usare esclusivamente una ROM originale ottenuta legalmente;
- l'indicazione di non distribuire ROM già modificate.

### Windows 7, 8 e 8.1

Per creare anche l'eseguibile legacy, avvia manualmente il workflow **Build GUI Windows Legacy** dalla scheda Actions e inserisci lo stesso tag nel campo `release_tag`. Il file verrà aggiunto alla release esistente.

### Avvio manuale senza tag

Puoi avviare **Build GUI Patcher** con `Run workflow` per provare la compilazione. In questo caso i pacchetti vengono caricati come artifact del workflow, ma non viene creata una release pubblica.

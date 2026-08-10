# Dragon Quest Monsters: Joker 2 Professional – Traduzione italiana

[![](https://img.shields.io/github/v/release/Lurpigi/DQMJ2Pro_Translation?include_prereleases&label=Release)](https://github.com/Lurpigi/DQMJ2Pro_Translation/releases/latest)
[![](https://img.shields.io/github/downloads/Lurpigi/DQMJ2Pro_Translation/total.svg)](https://github.com/Lurpigi/DQMJ2Pro_Translation/releases)

[Original English README](README_EN.md)

Questa repository contiene la traduzione italiana amatoriale di **Dragon Quest Monsters: Joker 2 Professional** e viene mantenuta anche per integrare gli aggiornamenti tecnici del progetto inglese.

> Il progetto non contiene ROM commerciali. Per giocare devi applicare la patch a una copia della ROM ottenuta legalmente.

[Scarica il patcher italiano](https://github.com/Lurpigi/DQMJ2Pro_Translation/releases) · [Annuncio della versione italiana](Guide/v1.0_announcement_post_it.md) · [Domande frequenti](Guide/faq_it.md)

<img src="./Database/credits.png" width="700" alt="Crediti del progetto originale">

## Il lavoro della community alla base del progetto

Questa traduzione italiana usa come base lo straordinario lavoro del [Dragon Quest Monsters: Joker 2 Professional English Translation Project](https://github.com/Saneezore/DQMJ2Pro_Translation). Senza questi bravissimi membri della community, realizzare la versione italiana sarebbe stato impossibile o avrebbe richiesto **mooolto** più tempo.

In particolare:

- [Ceris White](https://github.com/CerisWhite) ha creato il [toolkit originale](https://github.com/CerisWhite/DQMJ2Pro_Translation) per modificare la ROM e inserire i testi, avviando la traduzione inglese insieme a Ilario e Reflex;
- [Saneezore](https://github.com/Saneezore) ha creato l'interfaccia grafica del patcher e mantenuto la versione moderna del progetto inglese;
- Gerb ha tradotto e localizzato il post-game;
- GemSlimee, TheTwistery e monkeyboy hanno revisionato e corretto i testi;
- Darko, Hoodinibobeenie e Anthcny hanno creato e bilanciato le nuove ricette di sintesi;
- [WireOn](https://github.com/Wire0n-misc/dqmj2-randomizer) ha realizzato il randomizzatore di DQMJ2 adattato al progetto;
- Mow della comunità [DS⁽ⁱ⁾ Mode Hacking](https://wiki.ds-homebrew.com/community/) ha implementato la nuova correzione anti-pirateria;
- il server Discord [Dragon Quest Translations](https://discord.gg/aX6Ac8cC84) ha ospitato e sostenuto la collaborazione originale.

L'elenco completo dei traduttori, revisori e tester è disponibile nella sezione [Crediti](#crediti) e nell'[annuncio italiano](Guide/v1.0_announcement_post_it.md). La documentazione inglese originale è stata mantenuta accanto alle nuove copie italiane nella cartella `Guide/`.

## Come è stata realizzata la traduzione italiana

La traduzione parte dai testi inglesi della versione Professional e li confronta, quando possibile, con i testi originali e con le lingue interne della versione normale europea di DQMJ2.

- Dialoghi, menu, descrizioni e nomi condivisi con la versione normale sono stati verificati contro la localizzazione italiana ufficiale.
- La terminologia ufficiale di DQMJ2 è stata privilegiata per mostri, mosse, abilità, tratti, oggetti, luoghi, personaggi e formule ricorrenti.
- I contenuti aggiunti o modificati in Professional sono stati tradotti manualmente conservando tono, stile e caratterizzazione dei personaggi.
- La [traduzione italiana di DQMJ3P](https://github.com/Lurpigi/DQMJ3P-IT-FanTranslation) è stata consultata soltanto come riferimento secondario per termini del franchise assenti da DQMJ2. I luoghi specifici di DQMJ3P non sono stati importati.
- I riferimenti negli script sono stati verificati nei comandi `SAY` e `SETNAME`, compresi i nomi parzialmente codificati.
- I dialoghi identici alla versione normale vengono recuperati direttamente dall'italiano ufficiale; quelli esclusivi di Professional vengono impaginati in base alle metriche reali del font NFTR.

I codici di controllo e i segnaposto, come `{NAME}`, `{E321}`, `{COLOR=...}`, `{WAIT}`, `{CLEAR}` e `{BREAK}`, fanno parte del formato originale e vengono mantenuti quando sono necessari al funzionamento del gioco.

## Patcher italiano

Il patcher grafico è disponibile per Windows, Linux e macOS nella pagina [Releases](https://github.com/Lurpigi/DQMJ2Pro_Translation/releases). Seleziona una ROM originale, scegli le opzioni desiderate e premi **Applica la patch**. La versione distribuita è autonoma e non richiede Python.

<img src="./Database/GUI_Patcher/gui.png" width="420" alt="Interfaccia grafica del patcher">

Per costruire e pubblicare personalmente il programma consulta la [guida italiana alle release](Guide/releasing_patcher_it.md).

## Guide italiane

- [Guida manuale per Windows](Guide/step-by-step_it.md)
- [Guida manuale per Linux](Guide/linux_guide_it.md)
- [Applicazione manuale della patch anti-pirateria](Guide/ap_patching_it.md)
- [Compatibilità con le flashcard R4](Guide/playing_on_r4_it.md)
- [Aggiunta delle nuove ricette di sintesi](Guide/adding_new_synths_it.md)
- [Domande frequenti](Guide/faq_it.md)
- [Creazione di una release del patcher](Guide/releasing_patcher_it.md)
- [Annuncio della versione italiana](Guide/v1.0_announcement_post_it.md)

Le versioni inglesi originali degli stessi documenti sono conservate nella cartella [`Guide/`](Guide/).

## Funzionalità

- Menu, storia, tutorial e contenuti post-game tradotti e localizzati in italiano.
- Terminologia basata soprattutto sulla traduzione italiana ufficiale della versione normale di DQMJ2.
- Nuove ricette di sintesi per mostri Wi-Fi o altrimenti non ottenibili.
- Interfaccia grafica per applicare facilmente la patch.
- Correzione anti-pirateria per hardware originale compatibile.
- Modifiche opzionali di qualità della vita e gameplay.
- Database italiani di sintesi, statistiche, tratti, abilità e resistenze.
- Randomizzatore con filtri per grado, famiglia e dimensione, randomizzazione dei PE e opzioni sfida.

## Problemi noti

- Alcune grafiche contenenti testo giapponese possono rimanere non tradotte: sono asset grafici, non normali stringhe di testo.
- Il randomizzatore può rendere il gioco instabile. Tre mostri da uno slot potrebbero, per esempio, diventare tre mostri da tre slot e causare un crash. Per una partita più stabile escludi i mostri da tre slot o fuggi dagli incontri opzionali problematici.
- Randomizzando le ricette di sintesi, alcuni risultati della famiglia `???` potrebbero non essere sintetizzabili. Se un risultato non mostra il nome, non selezionarlo.
- Quando il nome originale di un mostro reclutato supera i 13 caratteri, la tastiera inferiore può mostrare un difetto grafico durante il ripristino del nome predefinito. Il problema è soltanto visivo.
- Alcuni vecchi firmware R4 non sono compatibili con la patch. Consulta la [guida italiana per R4](Guide/playing_on_r4_it.md).

## Struttura dei file

- `Translation/SCRIPTS/`: dialoghi, eventi, tutorial e post-game; vengono tradotti sia i testi `SAY` sia i nomi `SETNAME`.
- `Translation/STRINGS/`: interfaccia, tabelle, nomi, descrizioni e messaggi di gioco.
- `Pro_Tools/`: strumenti per estrarre, modificare, ricostruire e verificare ROM, stringhe e script. `format_dialogues.py` controlla l'impaginazione usando le larghezze reali dei glifi NFTR e conserva i controlli originali quando possibile.
- `game/rom/`: estrazione della versione normale usata come riferimento per l'italiano ufficiale.
- `game/romP/`: estrazione della versione Professional usata per individuare differenze e contenuti aggiuntivi.
- `game/tmp/`: strumenti riproducibili di confronto, importazione e controllo. In particolare, `import_legend_terms.py` importa soltanto corrispondenze esatte dalla legenda italiana di DQMJ3P ed esclude intenzionalmente i luoghi; `make_italian_databases.py` rigenera le copie italiane dei database; gli altri script documentano verifiche e correzioni mirate eseguite durante la traduzione.
- `Database/GUI_Patcher/GUI/`: sorgenti dell'interfaccia del patcher, del backend e del randomizzatore localizzati in italiano.
- `Database/`: database inglesi originali, copie italiane e glossari inglese→italiano.
- `Guide/`: documentazione originale inglese e traduzioni italiane.

## Database italiani e glossari

I database inglesi originali sono stati mantenuti. Le copie con suffisso `_it` permettono di consultare statistiche e ricette usando la terminologia italiana.

- [`monster_database_it.csv`](Database/monster_database_it.csv): statistiche, grado, famiglia, abilità e tratti.
- [`monster_resistance_database_it.csv`](Database/monster_resistance_database_it.csv): resistenze dei mostri.
- [`synthesis_database_it.html`](Database/synthesis_database_it.html): ricette consultabili e ricercabili nel browser; disponibile direttamente [Qui](https://lurpigi.github.io/DQMJ2Pro_Translation/).
- [`synthesis_database_it.csv`](Database/synthesis_database_it.csv): ricette in formato CSV.
- [`monster_ids_it.csv`](Database/monster_ids_it.csv): corrispondenza fra ID e nomi italiani.
- [`new_synths_4g_it.csv`](Database/new_synths_4g_it.csv) e [`new_synths_kind_it.csv`](Database/new_synths_kind_it.csv): ricette aggiuntive.
- [`postgame_pipit_vendor_items_it.csv`](Database/postgame_pipit_vendor_items_it.csv): oggetti del mercante Pipit nel post-game.

I glossari `translation_*.csv` documentano le corrispondenze inglese→italiano per mostri, mosse, abilità, tratti, oggetti, luoghi e personaggi. Servono per controllare la coerenza e non vengono importati direttamente nella ROM.

## Crediti

### Sviluppo tecnico originale

- [Ceris White](https://github.com/CerisWhite): toolkit Python per la modifica della ROM e l'inserimento dei testi.
- [Saneezore](https://github.com/Saneezore): interfaccia grafica del patcher.
- Mow: implementazione della patch anti-pirateria per l'overlay 4.
- [WireOn](https://github.com/Wire0n-misc/dqmj2-randomizer): randomizzatore originale adattato al progetto.

### Traduzione e localizzazione inglese

- Ceris White, Ilario e Reflex: importazione dei testi esistenti e traduzione dei menu.
- Gerb: traduzione e localizzazione dei contenuti post-game.
- GemSlimee, TheTwistery e monkeyboy: revisione e correzione.

### Nuove ricette di sintesi

- Darko, Hoodinibobeenie e Anthcny: nuove ricette e bilanciamento.

### Test del progetto originale

Ilario, Reflex, Gerb, Darko, GemSlimee, Hoodinibobeenie, Mad Raigo, Matthew McConville, Nurfed, Chris, diortememirp, Nightaura, Sloppydeck, Anti-Tank Guided Missile, Ghostface, Blark, Tifa'sLover, Samwise e oho.

### Traduzione italiana

- Lurpigi: traduzione, adattamento della terminologia ufficiale italiana, revisione degli script, localizzazione del patcher e mantenimento della fork italiana.
- [DQMJ3P-IT-FanTranslation](https://github.com/Lurpigi/DQMJ3P-IT-FanTranslation): riferimento secondario per la terminologia del franchise non presente in DQMJ2.

### Community

- [Dragon Quest Translations](https://discord.gg/aX6Ac8cC84): collaborazione e supporto del progetto inglese.
- [DS⁽ⁱ⁾ Mode Hacking](https://wiki.ds-homebrew.com/community/): supporto tecnico relativo alla patch anti-pirateria.

Grazie ancora a tutti gli autori del progetto inglese: questa versione italiana esiste grazie al loro lavoro.

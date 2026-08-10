## Applicare la patch anti-pirateria alla ROM

L'assenza di Eugene Poole, l'anziano sulla volonave, è una delle misure anti-pirateria inserite dagli sviluppatori. Il patcher grafico incluso nel progetto applica automaticamente una correzione compatibile con l'hardware originale; questa guida serve soltanto a chi utilizza la vecchia procedura manuale.

Il problema si manifesta su hardware reale, come Nintendo DS e Nintendo 3DS, ma generalmente non negli emulatori DeSmuME e melonDS.

![Applicazione della patch anti-pirateria per hardware reale](a.png)

### Passaggio 1

Scarica RetroGameFan NDS ROM Tool da [GBAtemp](https://gbatemp.net/download/retrogamefan-nds-rom-tool-v1-0_b1215.35735/).

### Passaggio 2

Estrai il programma, avvialo e premi il pulsante con i tre puntini (`...`) per aprire la ROM.

- Se compare `Validated Rom` in un riquadro verde, puoi continuare.
- Se compare `AP Patched` in un riquadro arancione, la ROM possiede già una patch AP: salta questa procedura e passa all'applicazione della traduzione.

Per la procedura manuale, copia quindi la ROM nella cartella principale del progetto e chiamala `DQMJ2P.nds`.

### Passaggio 3

Apri la scheda `Export`, verifica che `AP Patch` sia abilitato e premi `Export ROM`.

Salva il risultato come `DQMJ2P.nds` nella cartella principale del progetto. Non abilitare altre opzioni, come `Trim Garbage`, e imposta `Repack Options` su `No Repack (.nds | .3ds)`.

> Nota: per le flashcard R4 datate potrebbe essere preferibile usare pico_launcher. Consulta la [guida italiana per R4](playing_on_r4_it.md).


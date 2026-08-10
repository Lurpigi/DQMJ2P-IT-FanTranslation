## Dragon Quest Monsters: Joker 2 Professional

### Guida rapida alla patch manuale su Windows

Questa guida deriva dal [documento Google originale](https://docs.google.com/document/d/1hYcnyBTjx02n6xiYTC_GZ14FXWaOdcHdTvIsb3KCaw4/edit) e dalla guida tecnica del progetto inglese. Per l'uso normale è consigliato il patcher grafico disponibile nelle [release italiane](https://github.com/Lurpigi/DQMJ2Pro_Translation/releases).

1. Installa [Python per Windows](https://www.python.org/downloads/windows/) e seleziona **Add python.exe to PATH** durante l'installazione.

   ![Aggiungi Python al PATH](1.png)

2. Scarica il codice dalla [repo italiana](https://github.com/Lurpigi/DQMJ2Pro_Translation). La base tecnica originale è disponibile nella [repo inglese](https://github.com/Saneezore/DQMJ2Pro_Translation).

   ![Scarica il codice della repository](2.png)

3. Procurati una copia compilata di `ndstool` oppure compilalo dai sorgenti. Il repository include una versione per Windows nella cartella `Database`.

   ![ndstool](3.png)

4. Nella cartella `Pro_Tools`, copia o rinomina `blz_win.exe` in `blz.exe`.

   ![Rinomina blz_win in blz](4.png)

5. Nella barra del percorso di Esplora file digita `cmd` e premi Invio per aprire il prompt nella cartella del progetto.

   ![Apri il prompt dei comandi](5.png)

6. Esegui `python --version`. Se compare il numero di versione, Python è installato correttamente.

   ![Verifica la versione di Python](6.png)

7. Crea la cartella `Pro_ROM` ed estrai la ROM ottenuta legalmente:

```bat
mkdir Pro_ROM
ndstool -x DQMJ2P.nds -7 Pro_ROM\arm7.bin -9 Pro_ROM\arm9.bin -d Pro_ROM\data -y Pro_ROM\overlay -t Pro_ROM\banner.bin -h Pro_ROM\header.bin -y7 Pro_ROM\y7.bin -y9 Pro_ROM\y9.bin
```

![Estrai la ROM](7.png)

8. Decomprimi `arm9.bin` per renderlo utilizzabile dagli strumenti:

```bat
python Pro_Tools\arm9tool.py decompress Pro_ROM\arm9.bin Pro_Tools\Pro_ARM9.bin
```

![Decomprimi arm9.bin](8.png)

9. Avvia l'applicazione automatica delle modifiche:

```bat
python Pro_Tools\performpatch.py
```

Se hai usato un nome diverso per la cartella estratta, inseriscilo quando viene richiesto.

![Avvia il patcher automatico](9.png)

10. Ricostruisci la ROM:

```bat
ndstool -c Patched.nds -7 Pro_ROM\arm7.bin -9 Pro_ROM\arm9.bin -d Pro_ROM\data -y Pro_ROM\overlay -t Pro_ROM\banner.bin -h Pro_ROM\header.bin -y7 Pro_ROM\y7.bin -y9 Pro_ROM\y9.bin
```

![Ricostruisci la ROM](10.png)

Al termine troverai `Patched.nds`, utilizzabile su un emulatore compatibile o su hardware reale configurato correttamente.

## Giocare con una flashcard R4

### In breve

Per molte R4 datate è necessario installare [pico_launcher](https://github.com/LNH-team/pico-launcher), perché i vecchi kernel possono bloccarsi su una schermata bianca all'avvio della ROM patchata.

### Procedura

1. Apri la [guida alle flashcard](https://sanrax.github.io/flashcart-guides/cart-guides/dspico/) e individua il tuo modello di R4. ![Esempio di selezione della flashcard](b.png)
2. Dopo aver salvato tutti i file importanti, [formatta la scheda SD](https://sanrax.github.io/flashcart-guides/tutorials/formatting/) e segui specificamente le istruzioni della scheda **pico_loader**.
3. Copia sulla scheda SD la ROM creata dal patcher.
4. Avvia il gioco.

### La mia R4 non compare nella guida

Nel corso degli anni sono stati prodotti moltissimi cloni R4 con hardware, firmware e kernel differenti; la compatibilità non può quindi essere garantita per ogni modello. Una possibile alternativa è una flashcard moderna [DSpico](https://www.lnh-team.org/), progettata con maggiore apertura verso gli sviluppatori e con supporto più uniforme.

### Perché è necessario?

Le vecchie patch anti-pirateria modificano direttamente alcuni punti della ROM. Determinati kernel R4 non gestiscono correttamente queste modifiche e si bloccano durante l'avvio. D'altra parte, le protezioni originali di Joker 2 Professional impediscono di proseguire normalmente nel gioco.

Pico_Loader applica invece le correzioni in modo dinamico usando gli ID e gli offset degli overlay. Questo approccio è generalmente più robusto e non richiede di applicare alla ROM le vecchie patch AP incompatibili.

La spiegazione tecnica originale di Mow è disponibile nella [versione inglese di questa guida](playing_on_r4.md). Mow fa parte della comunità [DS⁽ⁱ⁾ Mode Hacking](https://wiki.ds-homebrew.com/community/), che ha contribuito alla soluzione anti-pirateria usata dal progetto.


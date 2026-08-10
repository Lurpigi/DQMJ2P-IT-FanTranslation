## Guida manuale per Linux

### Requisiti

`python3` `ndstool` `wine`

### Arch Linux, CachyOS ed EndeavourOS

```bash
sudo pacman -S python wine
```

```bash
yay -S ndstool
```

### Debian, Linux Mint e Ubuntu

```bash
sudo apt install -y python3 wine build-essential
```

```bash
wget https://github.com/devkitPro/ndstool/releases/download/v2.1.2/ndstool-2.1.2.tar.bz2
tar -xjf ndstool-2.1.2.tar.bz2
cd ndstool-2.1.2
./configure && make && sudo make install
```

### Preparazione del progetto

```bash
git clone https://github.com/Lurpigi/DQMJ2Pro_Translation
cd DQMJ2Pro_Translation
mkdir -p Pro_ROM
cp Pro_Tools/blz_win.exe Pro_Tools/blz.exe
```

Copia la ROM ottenuta legalmente nella cartella del progetto e chiamala `DQMJ2P.nds`.

```bash
ndstool -x DQMJ2P.nds -7 Pro_ROM/arm7.bin -9 Pro_ROM/arm9.bin -d Pro_ROM/data -y Pro_ROM/overlay -t Pro_ROM/banner.bin -h Pro_ROM/header.bin -y7 Pro_ROM/y7.bin -y9 Pro_ROM/y9.bin
```

```bash
python3 Pro_Tools/arm9tool.py decompress Pro_ROM/arm9.bin Pro_Tools/Pro_ARM9.bin
python3 Pro_Tools/performpatch.py --rom Pro_ROM
```

<details>
<summary>Aggiungere le nuove ricette di sintesi</summary>

Segui la [guida italiana dedicata](adding_new_synths_it.md) prima di ricostruire la ROM.

</details>

```bash
ndstool -c Patched.nds -7 Pro_ROM/arm7.bin -9 Pro_ROM/arm9.bin -d Pro_ROM/data -y Pro_ROM/overlay -t Pro_ROM/banner.bin -h Pro_ROM/header.bin -y7 Pro_ROM/y7.bin -y9 Pro_ROM/y9.bin
```

Per la maggior parte degli utenti è consigliato il patcher grafico distribuito nelle [release della fork italiana](https://github.com/Lurpigi/DQMJ2Pro_Translation/releases).

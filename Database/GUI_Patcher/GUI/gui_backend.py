#!/usr/bin/env python3
import argparse
import csv
import atexit
import os
import importlib.util
import shutil
import subprocess
import struct
import sys
from pathlib import Path
import tempfile


# Il backend può essere eseguito dalla console Windows, che spesso usa cp1252.
# Le utility condivise riportano alcuni simboli Unicode; usa UTF-8 quando
# l'output supporta la riconfigurazione, evitando che il log interrompa il patch.
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def run(cmd, cwd=None):
    print("> " + " ".join(map(str, cmd)), flush=True)

    creationflags = 0
    startupinfo = None

    if sys.platform.startswith("win"):
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    p = subprocess.run(
        [str(x) for x in cmd],
        cwd=cwd,
        creationflags=creationflags,
        startupinfo=startupinfo,
    )

    if p.returncode != 0:
        raise SystemExit(p.returncode)


def app_root():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def run_py_script(script_path, argv):
    script_path = Path(script_path).resolve()
    old_argv = sys.argv[:]
    old_cwd = Path.cwd()
    try:
        sys.argv = [str(script_path)] + [str(a) for a in argv]
        os.chdir(script_path.parent)
        spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "main"):
            mod.main()
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv


def inject_splash_assets(root, data_dir):
    splash_dir = root / "splash"
    if not splash_dir.is_dir():
        print(f"AVVISO: cartella delle grafiche iniziali mancante: {splash_dir}")
        return

    files = [
        "warning.chr",
        "warning.pal",
        "warning_lo.scrn",
        "warning_up.scrn",
    ]

    print("Inserimento delle grafiche iniziali personalizzate...")

    for name in files:
        src = splash_dir / name
        dst = Path(data_dir) / name

        if not src.is_file():
            raise SystemExit(f"Grafica iniziale mancante: {src}")

        shutil.copy2(src, dst)
        print(f"  {name} -> {dst}")



TILE_SIZE_4BPP = 32


def ncgr_tile_data_offset(data: bytes) -> int:
    block = data.find(b"RGCN")
    if block < 0:
        raise RuntimeError("Blocco RGCN non trovato")
    if data[block + 16:block + 20] != b"RAHC":
        raise RuntimeError("Firma del blocco NCGR non valida")
    return block + 16 + 32


def copy_ncgr_tiles(path: Path, src_tile: int, dst_tile: int, n_tiles: int, label: str) -> None:
    data = bytearray(path.read_bytes())
    tile_off = ncgr_tile_data_offset(data)

    src = tile_off + src_tile * TILE_SIZE_4BPP
    dst = tile_off + dst_tile * TILE_SIZE_4BPP
    n_bytes = n_tiles * TILE_SIZE_4BPP

    data[dst:dst + n_bytes] = data[src:src + n_bytes]
    path.write_bytes(bytes(data))

    print(
        f"  {label}: tile modificate {dst_tile}-{dst_tile + n_tiles - 1} "
        f"<- tile {src_tile}-{src_tile + n_tiles - 1} in {path}"
    )


def apply_baked_graphic_text_fixes(data_dir: Path) -> None:
    """Copy already-present English baked glyph tiles over Japanese baked glyph tiles."""
    print("Applicazione delle correzioni al testo incorporato nelle grafiche...")

    copy_ncgr_tiles(
        data_dir / "d2_ObjBattleData.bin",
        src_tile=136,
        dst_tile=128,
        n_tiles=8,
        label="messaggio MISS in battaglia",
    )

    copy_ncgr_tiles(
        data_dir / "d2_ObjNaviMapData.bin",
        src_tile=17,
        dst_tile=4,
        n_tiles=3,
        label="pulsante Menu della mappa",
    )

def find_ndstool(root, repo):
    if sys.platform.startswith("win"):
        bundled = root / "bundled" / "tools" / "windows" / "ndstool.exe"
    elif sys.platform == "darwin":
        bundled = root / "bundled" / "tools" / "macos" / "ndstool"
    else:
        bundled = root / "bundled" / "tools" / "linux" / "ndstool"

    if bundled.exists():
        return bundled

    if sys.platform.startswith("win"):
        db_tool = repo / "Database" / "ndstool.exe"
        if db_tool.exists():
            return db_tool

    found = shutil.which("ndstool")
    if found:
        return Path(found)

    raise SystemExit("ndstool non è stato trovato.")

AP_PATCHES = [
    (0x00004500,
     "AB 6C 48 42 E2 00 9B 10 0E E3 62 A1 B4 96 67 FB",
     "00 00 9F E5 1E FF 2F E1 83 A8 00 00 07 40 2D E9"),
    (0x00004510,
     "F8 E8 C7 E2 A8 E1 87 76 96 9D F5 6C A0 3C F0 1A",
     "14 00 9F E5 14 10 9F E5 00 20 91 E5 02 00 50 E1"),
    (0x00004520,
     "FA B2 CF B2 13 94 FE 10 9C 6B 4A 11 C4 5A 4F F3",
     "0C 00 9F 05 00 00 81 05 07 80 BD E8 EC 90 1D 02"),
    (0x00004530,
     "C9 D3 5E 75 00 6E 0B C7",
     "C8 88 1D 02 00 15 00 02"),
    (0x000049F8,
     "1E FF 2F E1",
     "C3 FE FF EA"),
]


def _hexbytes(s):
    return bytes.fromhex(s.replace(" ", ""))


def apply_antipiracy_patch(input_rom, work_dir):
    src = Path(input_rom)
    dst = Path(work_dir) / "input_antipiracy.nds"
    shutil.copy2(src, dst)

    data = bytearray(dst.read_bytes())

    print("Applicazione della patch anti-pirateria per l'hardware originale...")

    for off, old_hex, new_hex in AP_PATCHES:
        old = _hexbytes(old_hex)
        new = _hexbytes(new_hex)
        cur = bytes(data[off:off + len(old)])

        if cur == new:
            print(f"  0x{off:08X}: già modificato")
            continue

        if cur != old:
            raise SystemExit(
                f"Dati inattesi durante la patch anti-pirateria all'indirizzo 0x{off:08X}. "
                "La ROM non corrisponde alla versione originale prevista di DQMJ2P "
                "oppure è già stata modificata in modo differente."
            )

        data[off:off + len(old)] = new
        print(f"  0x{off:08X}: modificato")

    dst.write_bytes(data)
    return dst



def apply_overlay4_antipiracy_patch(ov4_path, overlay_decompress, overlay_compress):
    ov4_path = Path(ov4_path)
    if not ov4_path.is_file():
        raise SystemExit(f"overlay_0004.bin non trovato: {ov4_path}")

    print("Applicazione della patch anti-pirateria a overlay_0004...")

    dec = overlay_decompress(ov4_path)

    if len(dec) < 0x1F8:
        raise SystemExit("Dopo la decompressione overlay_0004.bin è più piccolo del previsto")

    ptr_154 = dec[0x154:0x158]
    ptr_1f4 = dec[0x1F4:0x1F8]

    old_150 = dec[0x150:0x154]
    old_1f0 = dec[0x1F0:0x1F4]

    dec[0x150:0x154] = ptr_154
    dec[0x1F0:0x1F4] = ptr_1f4

    print(f"  overlay_0004 +0x150: {old_150.hex(' ')} -> {ptr_154.hex(' ')}")
    print(f"  overlay_0004 +0x1F0: {old_1f0.hex(' ')} -> {ptr_1f4.hex(' ')}")

    ov4_path.write_bytes(overlay_compress(bytes(dec)))


def _csv_set(value):
    return {x.strip() for x in str(value).split(",") if x.strip()}



def build_randomizer_settings_summary(args):
    state = lambda enabled: "attivo" if enabled else "disattivato"
    lines = [
        "",
        "--- Impostazioni del patcher ---",
        "Opzioni della patch:",
        "- Anti-pirateria: attiva",
        f"- Nuove ricette di sintesi: {state(args.new_synths)}",
        f"- Oggetti del mercante Pipit nel post-game: {state(args.postgame_pipit_vendor_items)}",
        f"- Suffissi X/XY dei mostri: {state(args.xvariant_suffix)}",
        f"- Icone del sesso: {state(args.gender_icons)}",
        f"- Moltiplicatore PE: {state(bool(args.xp_mult))}",
        f"- Scouting dopo l'offesa: {state(args.scout_offense)}",
        f"- Modifiche alle penalità di scouting: {state(args.scout_penalty)}",
        f"- Modifiche al livello di sintesi: {state(bool(args.synthesis_level))}",
        f"- Modifiche alla polarità di sintesi: {state(args.synthesis_polarity)}",
        "",
        "Impostazioni del randomizzatore:",
        f"- Mostri negli incontri: {state(args.randomizer_monsters)}",
        f"- PE delle battaglie: {state(args.randomizer_xp)}",
        f"- Registro spoiler: {state(args.randomizer_spoiler)}",
        f"- Consenti Fuga/Scout: {state(args.randomizer_allow_flee)}",
        f"- Mostri più forti: {state(args.randomizer_stronger)}",
        f"- Vietata la fuga: {state(args.randomizer_no_flee)}",
        f"- Modalità PE per livello: {args.randomizer_level_up}",
        f"- Variazione PE per livello: {args.randomizer_level_up_variance}",
        f"- Modalità punti abilità: {args.randomizer_skill_points}",
        f"- Set di abilità: {state(args.randomizer_skillsets)}",
        f"- Sintesi generica: {state(args.randomizer_generic_synthesis)}",
        f"- Gradi esclusi: {args.randomizer_rank_excludes or 'nessuno'}",
        f"- Famiglie escluse: {args.randomizer_family_excludes or 'nessuna'}",
        f"- Dimensioni escluse: {args.randomizer_size_excludes or 'nessuna'}",
        "- Incontri da 0 PE: sempre ignorati",
        "",
    ]

    return "\n".join(lines)

def apply_postgame_pipit_vendor_items(repo: Path, pro_rom: Path):
    csv_path = repo / "Database" / "postgame_pipit_vendor_items.csv"
    store_path = pro_rom / "data_dir" / "StoreTbl_B.bin"

    if not csv_path.is_file():
        raise SystemExit(f"CSV del mercante Pipit nel post-game non trovato: {csv_path}")
    if not store_path.is_file():
        raise SystemExit(f"StoreTbl_B.bin non trovato: {store_path}")

    data = bytearray(store_path.read_bytes())
    if data[:4] != b"STRE":
        raise SystemExit(f"Firma di StoreTbl_B inattesa in {store_path}")

    count = struct.unpack_from("<I", data, 4)[0]

    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    changed = 0
    for row in rows:
        item_id = int(row["ID"], 0)
        rank = int(row["Rank"], 0)
        for_sale = int(row["ForSale"], 0)

        if item_id < 0 or item_id >= count:
            raise SystemExit(f"ID oggetto del mercante Pipit fuori intervallo: {item_id}")

        off = 8 + item_id * 4
        old = struct.unpack_from("<HBB", data, off)
        new = (rank, for_sale, 0)
        struct.pack_into("<HBB", data, off, *new)

        if old != new:
            changed += 1
            print(f"  item {item_id:>3} {row.get('Name', '')}: {old[0]},{old[1]} -> {rank},{for_sale}")

    store_path.write_bytes(data)
    print(f"  aggiornate {changed} voci di StoreTbl_B")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Backend del patcher grafico di DQMJ2P")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--work", default=None)
    ap.add_argument("--keep-work", action="store_true", help="Non eliminare GUI_WORK dopo la patch")
    ap.add_argument("--repo", default="AUTO")

    ap.add_argument("--new-synths", action="store_true")
    ap.add_argument("--postgame-pipit-vendor-items", action="store_true")
    ap.add_argument("--anti-piracy", action="store_true")
    ap.add_argument("--xp-mult", type=float, default=None)
    ap.add_argument("--xvariant-suffix", action="store_true")
    ap.add_argument("--gender-icons", action="store_true")
    ap.add_argument("--scout-offense", action="store_true")
    ap.add_argument("--scout-penalty", action="store_true")
    ap.add_argument("--synthesis-level", type=int, default=None)
    ap.add_argument("--synthesis-polarity", action="store_true")

    ap.add_argument("--randomizer-monsters", action="store_true")
    ap.add_argument("--randomizer-seed", type=int, default=0)
    ap.add_argument("--randomizer-spoiler", action="store_true")
    ap.add_argument("--randomizer-allow-flee", action="store_true")
    ap.add_argument("--randomizer-remove-zero-xp", action="store_true")
    ap.add_argument("--randomizer-xp", action="store_true")
    ap.add_argument("--randomizer-stronger", action="store_true")
    ap.add_argument("--randomizer-no-flee", action="store_true")
    ap.add_argument("--randomizer-level-up", choices=["none", "swap", "random"], default="none")
    ap.add_argument("--randomizer-level-up-variance", type=int, default=110)
    ap.add_argument("--randomizer-skill-points", choices=["none", "swap", "random"], default="none")
    ap.add_argument("--randomizer-skillsets", action="store_true")
    ap.add_argument("--randomizer-generic-synthesis", action="store_true")
    ap.add_argument("--randomizer-rank-excludes", default="")
    ap.add_argument("--randomizer-family-excludes", default="")
    ap.add_argument("--randomizer-size-excludes", default="")

    args = ap.parse_args(argv)

    root = app_root()
    if args.repo == "AUTO":
        bundled_repo = root / "bundled" / "repo"
        repo = bundled_repo if bundled_repo.exists() else Path(__file__).resolve().parents[3]
    else:
        repo = Path(args.repo).resolve()

    rom = Path(args.rom).resolve()
    output = Path(args.output).resolve()
    if args.work is None and sys.platform == "darwin":
        work = Path(tempfile.mkdtemp(prefix="DQMJ2P_GUI_WORK_"))
    elif args.work is None:
        work = Path("GUI_WORK").resolve()
    else:
        work = Path(args.work).expanduser().resolve()
    pro_rom = work / "Pro_ROM"

    def _cleanup_work():
        if args.keep_work:
            print(f"Cartella di lavoro conservata: {work}")
            return
        try:
            if work.exists():
                shutil.rmtree(work)
                print(f"Cartella di lavoro eliminata: {work}")
        except Exception as e:
            print(f"AVVISO: impossibile eliminare la cartella di lavoro {work}: {e}")

    atexit.register(_cleanup_work)

    tools_repo = repo

    sys.path.insert(0, str(tools_repo / "Pro_Tools"))

    import msgtool
    import storytool
    from apply_patches import (
        arm9_decompress, arm9_compress,
        overlay_decompress, overlay_compress,
        update_y9,
        apply_grow_msg_pool,
        apply_grow_actionhelp,
        apply_xp_mult,
        apply_xvariant_suffix,
        apply_gender_icons,
        apply_scout_offense,
        apply_scout_penalty,
        apply_synthesis_level,
        apply_synthesis_polarity,
        find_rom,
    )

    if not rom.is_file():
        raise SystemExit(f"ROM non trovata: {rom}")

    ndstool = find_ndstool(root, repo)

    if work.exists():
        shutil.rmtree(work)
    pro_rom.mkdir(parents=True)

    if sys.platform == "darwin":
        tools_repo = work / "writable_repo"
        shutil.copytree(repo / "Pro_Tools", tools_repo / "Pro_Tools")
        for name in ("Translation", "Database"):
            src = repo / name
            dst = tools_repo / name
            if src.exists():
                shutil.copytree(src, dst)

        sys.path.insert(0, str(tools_repo / "Pro_Tools"))

        # Reload tool modules from the writable macOS copy so module-level
        # temp paths like Pro_ARM9.bin point inside the work dir.
        for mod_name in ("msgtool", "storytool", "apply_patches"):
            sys.modules.pop(mod_name, None)

        import msgtool
        import storytool
        from apply_patches import (
            arm9_decompress, arm9_compress,
            overlay_decompress, overlay_compress,
            update_y9,
            apply_grow_msg_pool,
            apply_grow_actionhelp,
            apply_xp_mult,
            apply_xvariant_suffix,
            apply_gender_icons,
            apply_scout_offense,
            apply_scout_penalty,
            apply_synthesis_level,
            apply_synthesis_polarity,
            find_rom,
        )

    print(f"ROM di origine: {rom}")
    print(f"ROM di destinazione: {output}")
    print(f"Cartella di lavoro: {work}")
    print()

    rom_for_extract = rom

    run([
        str(ndstool), "-x", str(rom_for_extract),
        "-7", str(pro_rom / "arm7.bin"),
        "-9", str(pro_rom / "arm9.bin"),
        "-d", str(pro_rom / "data_dir"),
        "-y", str(pro_rom / "overlay_dir"),
        "-t", str(pro_rom / "banner.bin"),
        "-h", str(pro_rom / "header.bin"),
        "-y7", str(pro_rom / "y7.bin"),
        "-y9", str(pro_rom / "y9.bin"),
        "-o", str(pro_rom / "logo.bin"),
    ])

    inject_splash_assets(root, pro_rom / "data_dir")
    apply_baked_graphic_text_fixes(pro_rom / "data_dir")

    print("Decompressione di ARM9 per gli strumenti testuali...")
    run_py_script(tools_repo / "Pro_Tools" / "arm9tool.py", [
        "decompress",
        pro_rom / "arm9.bin",
        tools_repo / "Pro_Tools" / "Pro_ARM9.bin",
    ])

    print("Ricostruzione delle stringhe...")
    msgtool.cmd_repack(str(repo / "Translation" / "STRINGS"), str(pro_rom / "data_dir"))

    print("Assemblaggio degli script...")
    storytool.cmd_asm(str(repo / "Translation" / "SCRIPTS"), str(pro_rom / "data_dir"))

    files = find_rom(pro_rom)

    print("Applicazione delle modifiche ad ARM9...")
    if "arm9" not in files:
        raise SystemExit("arm9.bin non trovato")
    arm9 = files["arm9"]
    dec = arm9_decompress(arm9)
    apply_grow_msg_pool(dec, 0x35000)
    if args.xvariant_suffix:
        apply_xvariant_suffix(dec)
    arm9.write_bytes(arm9_compress(dec))

    print("Applicazione delle modifiche a overlay_0001...")
    if "ov0001" not in files or "y9" not in files:
        raise SystemExit("overlay_0001.bin o y9.bin non trovato")
    ov1 = files["ov0001"]
    orig = ov1.stat().st_size
    dec = overlay_decompress(ov1)

    # TEMP crash workaround: disable actionhelp growth pending proper fix.
    # apply_grow_actionhelp(dec)
    if args.xp_mult is not None:
        apply_xp_mult(dec, args.xp_mult)

    if args.scout_offense:
        apply_scout_offense(dec)
    if args.scout_penalty:
        apply_scout_penalty(dec)

    comp = overlay_compress(bytes(dec))
    ov1.write_bytes(comp)
    if len(comp) != orig:
        update_y9(files["y9"], 1, len(comp))

    if args.synthesis_level is not None or args.synthesis_polarity:
        print("Applicazione delle modifiche a overlay_0000...")
        if "ov0000" not in files:
            raise SystemExit("overlay_0000.bin non trovato")
        ov0 = files["ov0000"]
        orig = ov0.stat().st_size
        dec = overlay_decompress(ov0)

        if args.synthesis_level is not None:
            apply_synthesis_level(dec, args.synthesis_level)
        if args.synthesis_polarity:
            apply_synthesis_polarity(dec)

        comp = overlay_compress(bytes(dec))
        ov0.write_bytes(comp)
        if len(comp) != orig:
            update_y9(files["y9"], 0, len(comp))

    if args.gender_icons:
        print("Sostituzione delle icone del sesso...")
        if "nftr" not in files:
            raise SystemExit("font_16x16.NFTR non trovato")
        apply_gender_icons(files["nftr"])

    if args.new_synths:
        print("Aggiunta delle nuove ricette di sintesi...")

        kind_csv = work / "Kind.csv"
        fourg_csv = work / "4g.csv"

        run_py_script(tools_repo / "Pro_Tools" / "synthesis_parser.py", [
            "--in", pro_rom / "data_dir" / "CombinationKindTbl.bin",
            "--out", kind_csv,
        ])

        run_py_script(tools_repo / "Pro_Tools" / "synthesis_parser.py", [
            "--in", pro_rom / "data_dir" / "Combination4GTbl.bin",
            "--out", fourg_csv,
            "--type", "4g",
        ])

        with open(kind_csv, "a", encoding="utf-8", newline="") as out:
            out.write((repo / "Database" / "new_synths_kind_it.csv").read_text(encoding="utf-8"))

        with open(fourg_csv, "a", encoding="utf-8", newline="") as out:
            out.write((repo / "Database" / "new_synths_4g_it.csv").read_text(encoding="utf-8"))

        run_py_script(tools_repo / "Pro_Tools" / "synthesis_parser.py", [
            "--in", kind_csv,
            "--out", pro_rom / "data_dir" / "CombinationKindTbl.bin",
        ])

        run_py_script(tools_repo / "Pro_Tools" / "synthesis_parser.py", [
            "--in", fourg_csv,
            "--out", pro_rom / "data_dir" / "Combination4GTbl.bin",
            "--type", "4g",
        ])

    if args.postgame_pipit_vendor_items:
        print("Aggiunta degli oggetti del mercante Pipit nel post-game...")
        apply_postgame_pipit_vendor_items(repo, pro_rom)

    if (
        args.randomizer_monsters
        or args.randomizer_xp
        or args.randomizer_level_up != "none"
        or args.randomizer_skill_points != "none"
        or args.randomizer_skillsets
        or args.randomizer_generic_synthesis
    ):
        sys.path.insert(0, str(root))
        from randomizer.pro_randomizer import ProRandomizerConfig, run_pro_randomizer

        randomizer_config = ProRandomizerConfig(
            seed=args.randomizer_seed,
            generate_spoiler=args.randomizer_spoiler,
            randomize_monsters=args.randomizer_monsters,
            allow_flee_scout=args.randomizer_allow_flee,
            remove_zero_xp=True,
            randomize_xp=args.randomizer_xp,
            stronger_monsters=args.randomizer_stronger,
            no_flee=args.randomizer_no_flee,
            level_up_mode=args.randomizer_level_up,
            level_up_variance=args.randomizer_level_up_variance,
            skill_points_mode=args.randomizer_skill_points,
            randomize_skillsets=args.randomizer_skillsets,
            randomize_generic_synthesis=args.randomizer_generic_synthesis,
            rank_excludes=_csv_set(args.randomizer_rank_excludes),
            family_excludes=_csv_set(args.randomizer_family_excludes),
            size_excludes=_csv_set(args.randomizer_size_excludes),
            settings_summary=build_randomizer_settings_summary(args),
        )

        run_pro_randomizer(
            pro_rom,
            output.parent,
            repo,
            randomizer_config,
            log=print,
        )


    if args.anti_piracy:
        ov4 = pro_rom / "overlay_dir" / "overlay_0004.bin"
        y9 = pro_rom / "y9.bin"
        if not ov4.is_file() or not y9.is_file():
            raise SystemExit("overlay_0004.bin o y9.bin non trovato")
        orig = ov4.stat().st_size
        apply_overlay4_antipiracy_patch(ov4, overlay_decompress, overlay_compress)
        if ov4.stat().st_size != orig:
            update_y9(y9, 4, ov4.stat().st_size)

    print("Ricostruzione della ROM...")
    run([
        str(ndstool), "-c", str(output),
        "-7", str(pro_rom / "arm7.bin"),
        "-9", str(pro_rom / "arm9.bin"),
        "-d", str(pro_rom / "data_dir"),
        "-y", str(pro_rom / "overlay_dir"),
        "-t", str(pro_rom / "banner.bin"),
        "-h", str(pro_rom / "header.bin"),
        "-y7", str(pro_rom / "y7.bin"),
        "-y9", str(pro_rom / "y9.bin"),
        "-o", str(pro_rom / "logo.bin"),
    ])

    print()
    print(f"Completato: {output}")


if __name__ == "__main__":
    main()

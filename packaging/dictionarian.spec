from pathlib import Path

import dictionarian_ai
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("dictionarian_ai")
core_parent = str(Path(dictionarian_ai.__file__).resolve().parent.parent)

analysis = Analysis(
    ["entrypoint.py"],
    pathex=["../src", core_parent],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        "dictionarian_cli.cli",
        "dictionarian_cli.provider",
        "dictionarian_ai.tools.db_adapters",
    ],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
executable = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="dictionarian",
    console=True,
    strip=False,
    upx=False,
)

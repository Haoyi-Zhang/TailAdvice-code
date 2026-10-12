#!/usr/bin/env python3
"""Render the analytic load boundary, without running scheduling experiments.

Requires Matplotlib. Computer Modern comes from Matplotlib's bundled TTF files,
so no TeX installation or host-specific font path is needed.
"""
from pathlib import Path
import csv
import shutil

import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager, pyplot as plt
import numpy as np

ARTIFACT = Path(__file__).resolve().parents[1]



def correct_cm_unicode():
    """Keep legacy CM glyphs but write their real Unicode PDF text mappings.

    Matplotlib's CM math fonts use TeX character slots, not Unicode slots.
    Correct only ToUnicode streams; vector paths, glyph shapes, and metrics
    remain untouched. FontTools is already a Matplotlib dependency.
    """
    from fontTools import agl
    from fontTools.ttLib import TTFont
    from matplotlib.backends.backend_pdf import PdfFile

    embed = PdfFile.embedTTF
    output = PdfFile.outputStream

    def write_stream(pdf, reference, data, *args, **kwargs):
        mapping = getattr(pdf, "_cm_text_mapping", None)
        if mapping is not None and isinstance(data, bytes) and b"begincmap" in data:
            entries = [
                f"<{code:04x}> <{value.encode('utf-16-be').hex()}>"
                for code, value in sorted(mapping.items())
            ]
            groups = [
                f"{len(entries[i:i+100])} beginbfchar\n"
                + "\n".join(entries[i:i+100]) + "\nendbfchar"
                for i in range(0, len(entries), 100)
            ]
            data = (
                "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
                "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
                "/CMapName /ComputerModernUnicode def\n/CMapType 2 def\n"
                "1 begincodespacerange\n<0000> <ffff>\nendcodespacerange\n"
                + "\n".join(groups)
                + "\nendcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n"
            ).encode("ascii")
        return output(pdf, reference, data, *args, **kwargs)

    def embed_font(pdf, filename, characters):
        mapping = None
        if Path(filename).name in ("cmr10.ttf", "cmmi10.ttf", "cmsy10.ttf", "cmex10.ttf"):
            with TTFont(filename) as font:
                cmap = font.getBestCmap()
                mapping = {code: agl.toUnicode(cmap[code]) for code in characters}
                if any(not value for value in mapping.values()):
                    raise ValueError("No Unicode name for a used Computer Modern glyph")
        pdf._cm_text_mapping = mapping
        try:
            return embed(pdf, filename, characters)
        finally:
            pdf._cm_text_mapping = None

    PdfFile.embedTTF = embed_font
    PdfFile.outputStream = write_stream

def configure_fonts():
    correct_cm_unicode()
    fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    for name in ("cmr10.ttf", "cmmi10.ttf", "cmsy10.ttf", "cmex10.ttf"):
        path = fonts / name
        if not path.is_file():
            raise FileNotFoundError(f"Matplotlib's bundled Computer Modern font: {name}")
        font_manager.fontManager.addfont(str(path))
    plt.rcParams.update({"font.family": "cmr10", "font.size": 8.97,
                         "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
                         "axes.unicode_minus": False, "text.usetex": False,
                         "pdf.fonttype": 42, "pdf.use14corefonts": False,
                         "axes.linewidth": 1.0, "xtick.labelsize": 7.97,
                         "ytick.labelsize": 7.97})


def main():
    configure_fonts()
    destination = ARTIFACT / "figures"
    destination.mkdir(parents=True, exist_ok=True)
    # The original PGFPlots domain and all 100 display samples are retained.
    rho = np.linspace(0.001, 0.905, 100)
    factor = 1 / (1 - rho)
    with (destination / "load-boundary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("rho", "C"))
        writer.writerows(zip(rho, factor))
    # Fixed PDF MediaBox and axis box match the current paper's measured geometry.
    fig = plt.figure(figsize=(336 / 72, 178 / 72))
    ax = fig.add_axes((31 / 336, 26 / 178, 304 / 336, 145 / 178))
    ax.plot(rho, factor, color="black", linestyle="--", linewidth=1.0)
    ax.set(xlim=(0, 0.92), ylim=(0.8, 11),
           xlabel=r"Load $\rho$", ylabel=r"Competitive factor $C$")
    ax.set_xticks((0, 0.2, 0.4, 0.6, 0.8), ("0", "0.2", "0.4", "0.6", "0.8"))
    ax.set_yticks((1, 3, 5, 7, 9, 11))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="out", width=1.0, length=2.5, pad=3)
    ax.text(0.25, 6.8, "Achievable by\nguarded sharing", ha="center", va="center")
    ax.text(0.65, 1.9, "Ruled out", ha="center", va="center")
    ax.text(0.79, 9.5, r"$C=1/(1-\rho)$", ha="right", va="center")
    target = destination / "load-boundary.pdf"
    fig.savefig(target, metadata={"Creator": None, "Producer": None,
                                  "CreationDate": None, "ModDate": None})
    plt.close(fig)
    # Both consumers use the same asset, including the standalone proof tree.
    for consumer in (ARTIFACT / "proofs" / "figures", ARTIFACT.parent / "paper" / "figures"):
        if consumer.is_dir():
            shutil.copyfile(target, consumer / target.name)
    print(f"Rendered analytic load boundary: {target}")


if __name__ == "__main__":
    main()

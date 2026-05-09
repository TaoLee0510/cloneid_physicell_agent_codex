from __future__ import annotations

from pathlib import Path
import zipfile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _paragraph(text: str) -> str:
    return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"


def _table(rows: list[list[str]]) -> str:
    xml_rows = []
    for row in rows:
        cells = []
        for cell in row:
            cells.append(f"<w:tc><w:p><w:r><w:t>{cell}</w:t></w:r></w:p></w:tc>")
        xml_rows.append(f"<w:tr>{''.join(cells)}</w:tr>")
    return f"<w:tbl>{''.join(xml_rows)}</w:tbl>"


def write_minimal_docx(path: Path, paragraphs: list[str], tables: list[list[list[str]]] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body_parts = [_paragraph(text) for text in paragraphs]
    for table in tables or []:
        body_parts.append(_table(table))
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}"><w:body>{"".join(body_parts)}</w:body></w:document>'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document)
        archive.writestr("word/media/image1.png", b"not-a-real-png-but-an-embedded-media-member")


def make_nwaa124_fixture_dir(base: Path) -> Path:
    supplement = base / "nwaa124_supplement_file"
    supplement.mkdir()
    figure_paragraphs = [
        "Supplementary Figure 1 | Fitness of r and K cells compared with IN cells.",
        "Mixed populations were measured over passages.",
        "Supplementary Figure 4 | Observed dynamics of mixed populations initiated with 90% r cells and 10% K cells.",
        "The bars represent the proportion change of cell population by time.",
        "Supplementary Figure 5 | Predicted dynamics of r and K cells mixed populations.",
        "Black boxes and lines represent simulation results. Gray boxes and lines represent observations.",
        "Supplementary Figure 6 | Detachment curves of r and K cells under trypsinization.",
        "Cells detached under trypsinization were counted every minute.",
        "Supplementary Figure 9 | Growth model fitting.",
        "Exponential (R- Squared number 0.739; p=3.02e-05), Gompertz (R- Squared number 0.828; p=7.7e-05) and Logistic (R- Squared number 0.856; p=4.95e-05).",
        "Supplementary Figure 10 | Carrying capacity estimation.",
        "The functions of density curve of r and K cells were estimated as 228280/(1+83.485 exp(-0.80585 x)) and 239120/(1+728.8 exp(-1.0549 x)), respectively.",
        "Supplementary Figure 11 | Predicted dynamics of r and K cells mixed populations.",
        "The populations were cultured under high density based on the density dependent population growth model.",
        "Supplementary Figure 12 | The dynamics of r and K cell mixture populations.",
        "Each panel shows 100 simulation predictions of a mixture population.",
        "Supplementary Figure 13 | The spatial computational model of population growth.",
        "The cell growth space was assumed to be a two-dimensional planar grid with migration, division, and density dependent regions.",
        "Supplementary Figure 14 | Density-dependent cell size.",
        "Fluorescence imaging of cells at two densities.",
        "Supplementary Figure 15 | Ratio of migrated cells.",
        "The data were collected using a trans-well migration assay.",
        "Supplementary Table 1 | The number of DEGs across comparisons.",
        "Supplementary Table 2 | Enrichment of DEGs in r and K cells under low-density.",
        "Supplementary Table 3 | Top 25 pathways enriched in r and K cells under crowed culture.",
        "Supplementary Table 5 |",
        "Supplementary Table 6 | The abbravations of KEGG patways in Figure 2d",
    ]
    tables = [
        [["Comparisons", "High-expressed genes number", "Low-expressed genes number", "Total DEGs number"], ["KL vs. rL", "1", "2", "3"]],
        [["KEGG Pathway", "Count", "%", "P-Value"], ["Spliceosome", "54", "1.7", "1.00E-10"]],
        [["Term", "Count", "%", "PValue", "Fold Enrichment"], ["Proteasome", "19", "1.0", "9.32E-09", "4.8"]],
        [
            ["Samples", "IN_G", "IN_R", "G3K", "R1K", "G3r", "R1r"],
            ["1", "1.1", "0.9", "1.0", "0.4", "1.2", "1.3"],
            ["2", "0.8", "1.0", "0.9", "0.5", "1.1", "1.4"],
        ],
        [["Abbravation", "Pathway"], ["AJ", "Adherens junction"]],
    ]
    write_minimal_docx(supplement / "Supplementary Figures and Tables revision_2nd.docx", figure_paragraphs, tables)
    write_minimal_docx(
        supplement / "Supplementary data- Materials and Methods.docx",
        [
            "Modeling population growth dynamics of r and K cells in a mixed population.",
            "The correlations are maximized when (, ) = (2.5,0).",
            "The spatial model uses a two-dimensional grid, migration, division, and density-dependent space.",
        ],
        [],
    )
    for name in ("Supplementary_Data_1.txt", "Supplementary_Data_2.txt", "Supplementary_Data_3.txt"):
        (supplement / name).write_text("Gene\tPPEE\tPPDE\tPostFC\tRealFC\nA\t0\t1\t1.1\t1.1\n")
    (supplement / "Supplementary_Data_4.vcf").write_text("##fileformat=VCFv4.2\n")
    return supplement


def make_nwaa124_fixture_zip(base: Path) -> Path:
    supplement = make_nwaa124_fixture_dir(base)
    zip_path = base / "nwaa124_supplement_file.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for path in sorted(supplement.iterdir()):
            archive.write(path, path.name)
    return zip_path

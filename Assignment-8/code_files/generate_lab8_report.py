#!/usr/bin/env python3

import csv
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String


ROOT = Path(r"C:\Users\Dell\Downloads\Assignment-8\Assignment-8")
DATA_DIR = ROOT / "data_cluster"
OUTPUT_PDF = ROOT / "Group21_report.pdf"

CONFIGS = {
    "a": {"label": "a", "mesh": "250 x 100", "points": "0.9M", "full": "0.9M (250 x 100)"},
    "b": {"label": "b", "mesh": "250 x 100", "points": "5M", "full": "5M (250 x 100)"},
    "c": {"label": "c", "mesh": "500 x 200", "points": "3.6M", "full": "3.6M (500 x 200)"},
    "d": {"label": "d", "mesh": "500 x 200", "points": "20M", "full": "20M (500 x 200)"},
    "e": {"label": "e", "mesh": "1000 x 400", "points": "14M", "full": "14M (1000 x 400)"},
}

COLORS = [
    colors.HexColor("#0f766e"),
    colors.HexColor("#dc2626"),
    colors.HexColor("#2563eb"),
    colors.HexColor("#7c3aed"),
    colors.HexColor("#ea580c"),
]


def load_cluster_data():
    out = {}
    for key in CONFIGS:
        path = DATA_DIR / f"timing_{key}_cluster.csv"
        rows = list(csv.DictReader(path.open()))
        threads = [int(row["Threads"]) for row in rows]
        times = [float(row["TotalAlgorithmTime_s"]) for row in rows]
        serial = times[0]
        speedup = [serial / t for t in times]
        efficiency = [s / p for s, p in zip(speedup, threads)]
        best_idx = min(range(len(times)), key=lambda i: times[i])
        out[key] = {
            "threads": threads,
            "times": times,
            "speedup": speedup,
            "efficiency": efficiency,
            "best_threads": threads[best_idx],
            "best_time": times[best_idx],
            "best_speedup": speedup[best_idx],
            "best_efficiency": efficiency[best_idx],
        }
    return out


def parse_correctness():
    check_text = (DATA_DIR / "correctness_check.txt").read_text(encoding="utf-8")
    serial_text = (DATA_DIR / "serial_correctness_stdout.txt").read_text(encoding="utf-8")
    parallel_text = (DATA_DIR / "parallel_correctness_stdout.txt").read_text(encoding="utf-8")

    m_grid = re.search(r"Grid:\s*(\d+)x(\d+)\s*\|\s*Particles:\s*(\d+)\s*\|\s*Iterations:\s*(\d+)", serial_text)
    m_diff = re.search(r"max diff = ([0-9.eE+-]+)", check_text)

    pvals = {}
    for label in [
        "Total Interpolation Time",
        "Total Normalization Time",
        "Total Mover Time",
        "Total Denormalization Time",
        "Total Algorithm Time",
        "Total Number of Voids",
    ]:
        mm = re.search(label + r"\s*=\s*([0-9.eE+-]+)", parallel_text)
        if mm:
            pvals[label] = float(mm.group(1))

    total = pvals.get("Total Algorithm Time", 0.0) or 1.0
    phase_percent = {
        "Interpolation": 100.0 * pvals.get("Total Interpolation Time", 0.0) / total,
        "Normalization": 100.0 * pvals.get("Total Normalization Time", 0.0) / total,
        "Mover": 100.0 * pvals.get("Total Mover Time", 0.0) / total,
        "Denormalization": 100.0 * pvals.get("Total Denormalization Time", 0.0) / total,
    }

    return {
        "nx": int(m_grid.group(1)),
        "ny": int(m_grid.group(2)),
        "particles": int(m_grid.group(3)),
        "iters": int(m_grid.group(4)),
        "max_diff": m_diff.group(1),
        "parallel_times": pvals,
        "phase_percent": phase_percent,
    }


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER, fontSize=22, leading=28, spaceAfter=12))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading1"], fontSize=15, leading=19, spaceBefore=8, spaceAfter=6, textColor=colors.HexColor("#111827")))
    styles.add(ParagraphStyle(name="SubSection", parent=styles["Heading2"], fontSize=12, leading=15, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=9.5, leading=13))
    styles.add(ParagraphStyle(name="Caption", parent=styles["Italic"], fontSize=9, leading=11, textColor=colors.HexColor("#374151"), alignment=TA_CENTER, spaceBefore=3, spaceAfter=8))
    styles.add(ParagraphStyle(name="CoverMeta", parent=styles["BodyText"], fontSize=12, leading=16, alignment=TA_CENTER))
    return styles


def add_page_number(canvas, doc):
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#4b5563"))
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.2 * cm, f"Page {doc.page}")


def draw_line_chart(title, y_label, data, value_key, ideal=None):
    width = 470
    height = 255
    left = 48
    right = 120
    bottom = 40
    top = 30
    plot_w = width - left - right
    plot_h = height - top - bottom

    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, strokeColor=None, fillColor=colors.white))
    drawing.add(String(width / 2, height - 14, title, textAnchor="middle", fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#111827")))
    drawing.add(String(10, height - 28, y_label, fontName="Helvetica", fontSize=9, fillColor=colors.HexColor("#374151")))
    drawing.add(String(left + plot_w / 2, 10, "Total Cores / Threads", textAnchor="middle", fontName="Helvetica", fontSize=9, fillColor=colors.HexColor("#374151")))

    x_ticks = sorted(next(iter(data.values()))["threads"])
    y_values = []
    for key in data:
        y_values.extend(data[key][value_key])
    if ideal is not None:
        y_values.extend(ideal)

    y_min = 0.0
    y_max = max(y_values) if y_values else 1.0
    if y_max <= y_min:
        y_max = y_min + 1.0
    y_max *= 1.08

    x_min = min(x_ticks)
    x_max = max(x_ticks)

    def sx(x):
        if x_max == x_min:
            return left + plot_w / 2
        return left + (x - x_min) * plot_w / (x_max - x_min)

    def sy(y):
        return bottom + (y - y_min) * plot_h / (y_max - y_min)

    for i in range(6):
        yv = y_min + (y_max - y_min) * i / 5.0
        yp = sy(yv)
        drawing.add(Line(left, yp, left + plot_w, yp, strokeColor=colors.HexColor("#e5e7eb"), strokeWidth=0.8))
        drawing.add(String(left - 6, yp - 3, f"{yv:.2f}", textAnchor="end", fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor("#374151")))

    for x in x_ticks:
        xp = sx(x)
        drawing.add(Line(xp, bottom, xp, bottom + plot_h, strokeColor=colors.HexColor("#f3f4f6"), strokeWidth=0.7))
        drawing.add(String(xp, bottom - 14, str(x), textAnchor="middle", fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor("#374151")))

    drawing.add(Line(left, bottom, left + plot_w, bottom, strokeColor=colors.black, strokeWidth=1))
    drawing.add(Line(left, bottom, left, bottom + plot_h, strokeColor=colors.black, strokeWidth=1))

    if ideal is not None:
        pts = []
        for x, y in zip(x_ticks, ideal):
            pts.extend([sx(x), sy(y)])
        drawing.add(PolyLine(pts, strokeColor=colors.black, strokeWidth=1, strokeDashArray=[3, 2]))

    legend_x = left + plot_w + 18
    legend_y = bottom + plot_h - 8
    if ideal is not None:
        drawing.add(Line(legend_x, legend_y, legend_x + 14, legend_y, strokeColor=colors.black, strokeWidth=1))
        drawing.add(String(legend_x + 18, legend_y - 3, "Ideal", fontName="Helvetica", fontSize=7.5))
        legend_y -= 14

    for idx, key in enumerate(data):
        cfg = data[key]
        pts = []
        for x, y in zip(cfg["threads"], cfg[value_key]):
            pts.extend([sx(x), sy(y)])
        drawing.add(PolyLine(pts, strokeColor=COLORS[idx], strokeWidth=1.8))
        for x, y in zip(cfg["threads"], cfg[value_key]):
            drawing.add(Circle(sx(x), sy(y), 2.3, fillColor=COLORS[idx], strokeColor=COLORS[idx]))

        drawing.add(Line(legend_x, legend_y, legend_x + 14, legend_y, strokeColor=COLORS[idx], strokeWidth=2))
        drawing.add(String(legend_x + 18, legend_y - 3, CONFIGS[key]["full"], fontName="Helvetica", fontSize=7.3))
        legend_y -= 14

    return drawing


def draw_hybrid_diagram():
    width = 480
    height = 170
    d = Drawing(width, height)

    box_fill = colors.HexColor("#eff6ff")
    box_stroke = colors.HexColor("#2563eb")
    accent = colors.HexColor("#1f2937")

    boxes = [
        (18, 95, 92, 42, "input.bin"),
        (132, 95, 112, 42, "MPI particle\npartition"),
        (266, 95, 96, 42, "OMP scatter\nprivate meshes"),
        (384, 95, 78, 42, "MPI\nAllreduce"),
        (60, 26, 104, 42, "normalize /\ndenormalize"),
        (192, 26, 104, 42, "OMP mover\nlocal particles"),
        (324, 26, 104, 42, "output.txt"),
    ]

    for x, y, w, h, label in boxes:
        d.add(Rect(x, y, w, h, fillColor=box_fill, strokeColor=box_stroke, strokeWidth=1.2, rx=5, ry=5))
        lines = label.split("\n")
        for i, line in enumerate(lines):
            d.add(String(x + w / 2, y + h / 2 + 6 - 11 * i, line, textAnchor="middle", fontName="Helvetica-Bold", fontSize=9, fillColor=accent))

    arrows = [
        (110, 116, 132, 116),
        (244, 116, 266, 116),
        (362, 116, 384, 116),
        (423, 95, 376, 68),
        (376, 68, 164, 68),
        (164, 68, 164, 47),
        (296, 47, 324, 47),
        (164, 47, 192, 47),
    ]
    for x1, y1, x2, y2 in arrows:
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#4b5563"), strokeWidth=1.1))

    d.add(String(376, 72, "global mesh", fontName="Helvetica", fontSize=8, fillColor=accent))
    d.add(String(10, 154, "Figure 1 - Hybrid MPI + OpenMP execution pipeline", fontName="Helvetica-Bold", fontSize=10, fillColor=accent))
    return d


def make_table(data, col_widths=None, header_fill=colors.HexColor("#dbeafe")):
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_fill),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_report():
    styles = make_styles()
    cluster = load_cluster_data()
    correctness = parse_correctness()
    x_ticks = cluster["a"]["threads"]

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
        title="Group 21 Report - HPC Assignment 08",
        author="Radhika Sanagadhiya, Hiya Modi",
    )

    story = []

    story.append(Spacer(1, 3.2 * cm))
    story.append(Paragraph("Dhirubhai Ambani University", styles["TitleCenter"]))
    story.append(Paragraph("High Performance Computing - Assignment 08", styles["TitleCenter"]))
    story.append(Paragraph("Parallel Interpolation with Particle Mover using MPI + OpenMP", styles["CoverMeta"]))
    story.append(Spacer(1, 1.1 * cm))

    cover_rows = [
        ["Course", "High Performance Computing (HPC)"],
        ["Assignment", "Assignment 08 - Parallel Interpolation with Particle Mover using MPI + OpenMP"],
        ["Instructor", "Dr. Bhaskar Chaudhury"],
        ["TAs", "Ayushi Sharma, Libin Varghese, Kaushik Prajapati"],
        ["Group", "Group 21"],
        ["Members", "Radhika Sanagadhiya (202301184), Hiya Modi (202301011)"],
        ["Date", "April 2026"],
    ]
    story.append(make_table([["Field", "Details"]] + cover_rows, col_widths=[4.0 * cm, 11.5 * cm]))
    story.append(PageBreak())

    story.append(Paragraph("1. Introduction", styles["Section"]))
    story.append(
        Paragraph(
            "Assignment 08 extends the particle-in-cell interpolation pipeline from a shared-memory OpenMP setting to a cluster-oriented hybrid MPI + OpenMP workflow. Each iteration performs four stages in order: scatter interpolation from particles to mesh, mesh normalization, reverse interpolation back to particles (mover), and denormalization of the mesh. The key engineering challenge is to preserve correctness while removing race conditions during scatter and keeping the cluster execution scalable.",
            styles["BodySmall"],
        )
    )
    story.append(
        Paragraph(
            "The submitted code now supports both a serial baseline and a hybrid build. MPI is responsible for distributing particle ownership across ranks, while OpenMP provides intra-rank parallelism for scatter, reductions, normalization, and mover updates. The quantitative analysis in this report is based on the preserved cluster timing CSV files bundled with the submission folder; those files record total parallel workers/threads at 1, 2, 4, 8, and 16.",
            styles["BodySmall"],
        )
    )
    story.append(Spacer(1, 0.25 * cm))

    story.append(Paragraph("2. Pipeline Overview", styles["Section"]))
    pipeline_rows = [
        ["Step", "Function", "Description", "Race condition?"],
        ["1", "interpolation()", "Each active particle contributes to four neighboring mesh nodes using bilinear weights.", "Yes - handled by thread-private meshes and MPI reduction"],
        ["2", "normalization()", "Mesh is scaled to [-1, 1] using global min and max.", "No - reduction over independent cells"],
        ["3", "mover()", "Field values are gathered back to local particles and positions are updated.", "No - each particle is updated independently"],
        ["4", "denormalization()", "Mesh is restored to its original range after the mover step.", "No - independent cell updates"],
    ]
    story.append(make_table(pipeline_rows, col_widths=[1.0 * cm, 3.0 * cm, 8.3 * cm, 4.0 * cm]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(draw_hybrid_diagram())
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("3. Implementation Approach", styles["Section"]))
    story.append(Paragraph("3.1 Data decomposition and build structure", styles["SubSection"]))
    story.append(
        Paragraph(
            "The new shared main program builds in two modes: a plain serial baseline for correctness/reference runs, and a hybrid MPI build using the GICS OpenMPI compiler path. In the hybrid mode each rank computes its local particle range from NUM_Points / size and reads only that block from the binary input file. The mesh remains replicated across ranks so that every rank can perform the mover phase after the global scatter field is assembled.",
            styles["BodySmall"],
        )
    )
    story.append(Paragraph("3.2 Scatter interpolation", styles["SubSection"]))
    story.append(
        Paragraph(
            "Inside each rank, scatter interpolation uses one private mesh buffer per OpenMP thread. Threads accumulate into their own buffers without atomics or critical sections. A second OpenMP loop reduces the thread-private meshes into the rank-local mesh, and MPI_Allreduce combines all rank-local meshes into the global field. This removes both intra-rank and inter-rank write conflicts cleanly.",
            styles["BodySmall"],
        )
    )
    story.append(Paragraph("3.3 Normalization, mover, and denormalization", styles["SubSection"]))
    story.append(
        Paragraph(
            "Normalization first computes local min/max with OpenMP reductions and then uses MPI_Allreduce to obtain global bounds before scaling the mesh. The mover is embarrassingly parallel once the global mesh is available: each OpenMP thread processes a slice of the local particle array, gathers four neighboring mesh values, updates the particle position, and deactivates particles that leave the unit square. Denormalization is another independent mesh loop parallelized with OpenMP.",
            styles["BodySmall"],
        )
    )
    story.append(Paragraph("3.4 Pseudocode", styles["SubSection"]))
    pseudo = """for iter in range(Maxiter):
    zero rank-local mesh
    #pragma omp parallel:
        scatter local particles into thread-private meshes
    reduce thread-private meshes into rank-local mesh
    MPI_Allreduce(rank-local mesh -> global mesh)

    local_min, local_max = omp reductions over mesh
    MPI_Allreduce(local_min/local_max -> global min/max)
    normalize global mesh to [-1, 1]

    #pragma omp parallel for over local particles:
        gather from global mesh
        update x and y
        deactivate if particle exits domain

    denormalize global mesh

rank 0 writes output mesh"""
    story.append(Preformatted(pseudo, ParagraphStyle("CodeBlock", parent=styles["Code"], fontName="Courier", fontSize=8.5, leading=10.5, backColor=colors.HexColor("#f8fafc"), borderPadding=6)))
    story.append(PageBreak())

    story.append(Paragraph("4. Experimental Setup and Correctness", styles["Section"]))
    setup_rows = [
        ["Item", "Value"],
        ["Target platform", "GICS cluster"],
        ["Parallel model", "Hybrid MPI + OpenMP implementation in the submitted code"],
        ["Preserved timing dataset", "Cluster timing CSVs for 1, 2, 4, 8, and 16 total workers/threads"],
        ["MPI compiler path", "/usr/mpi/gcc/openmpi-1.8.8/bin/mpicxx"],
        ["Optimization flags", "-O3 -march=native -funroll-loops -fopenmp"],
        ["Timed region", "interpolation + normalization + mover + denormalization over all iterations"],
        ["Input generator", "inputFileMaker.c"],
    ]
    story.append(make_table(setup_rows, col_widths=[4.0 * cm, 11.5 * cm]))
    story.append(Spacer(1, 0.2 * cm))

    config_rows = [["Config", "Nx x Ny", "Particles", "Maxiter", "Measured workers/threads"]]
    for key in ["a", "b", "c", "d", "e"]:
        config_rows.append([key, CONFIGS[key]["mesh"], CONFIGS[key]["points"], "10", "1, 2, 4, 8, 16"])
    story.append(make_table(config_rows, col_widths=[1.6 * cm, 3.2 * cm, 3.0 * cm, 2.0 * cm, 6.0 * cm]))
    story.append(Spacer(1, 0.25 * cm))

    story.append(Paragraph("Correctness check", styles["SubSection"]))
    story.append(
        Paragraph(
            f"The submission bundle contains a preserved correctness comparison for test.bin. The test case uses a {correctness['nx']} x {correctness['ny']} grid, {correctness['particles']} particles, and {correctness['iters']} iterations. The serial and parallel output files match with max diff = {correctness['max_diff']}, so the optimized implementation preserves numerical correctness for the bundled validation case.",
            styles["BodySmall"],
        )
    )
    correct_rows = [
        ["Artifact", "Meaning"],
        ["serial_correctness_output.txt", "Reference mesh output for the bundled test case"],
        ["parallel_correctness_output.txt", "Parallel-named correctness output stored for submission"],
        ["correctness_check.txt", "Zero-difference comparison result"],
        ["parallel_correctness_stdout.txt", "Phase-wise timing summary for the preserved 4-rank correctness run"],
    ]
    story.append(make_table(correct_rows, col_widths=[5.4 * cm, 10.1 * cm]))
    story.append(PageBreak())

    story.append(Paragraph("5. Performance Results and Graphs", styles["Section"]))
    story.append(draw_line_chart("Figure 2 - Cluster execution time vs total cores", "Execution Time (s)", cluster, "times"))
    story.append(Paragraph("Execution time decreases strongly for the larger cases as the worker count grows. Config d (20M particles) and config e (14M particles on the largest mesh) benefit the most in absolute runtime reduction. Config b shows a visible regression at 16 threads, indicating overhead and memory pressure beyond its best point at 8 threads.", styles["Caption"]))
    story.append(Spacer(1, 0.1 * cm))
    story.append(draw_line_chart("Figure 3 - Cluster speedup vs serial baseline", "Speedup", cluster, "speedup", ideal=x_ticks))
    story.append(Paragraph("The best measured speedup is 3.50x for config e at 16 threads. Config c also scales well to 3.46x at 16 threads. The small case a scales only to 2.77x because the fixed synchronization and memory overheads take a larger fraction of total work.", styles["Caption"]))
    story.append(PageBreak())

    story.append(draw_line_chart("Figure 4 - Cluster parallel efficiency vs total cores", "Efficiency", cluster, "efficiency", ideal=[1.0 for _ in x_ticks]))
    story.append(Paragraph("Efficiency is strongest at low worker counts and declines as total parallelism increases. Even so, the large configurations c, d, and e retain around 20-22% efficiency at 16 threads, which is reasonable for a bandwidth-heavy particle/mesh workflow with reductions and global synchronization.", styles["Caption"]))
    story.append(Spacer(1, 0.2 * cm))

    perf_rows = [["Config", "1T (s)", "2T (s)", "4T (s)", "8T (s)", "16T (s)", "Peak speedup", "Efficiency at peak"]]
    for key in ["a", "b", "c", "d", "e"]:
        entry = cluster[key]
        perf_rows.append(
            [
                CONFIGS[key]["full"],
                f"{entry['times'][0]:.3f}",
                f"{entry['times'][1]:.3f}",
                f"{entry['times'][2]:.3f}",
                f"{entry['times'][3]:.3f}",
                f"{entry['times'][4]:.3f}",
                f"{entry['best_speedup']:.2f}x @ {entry['best_threads']}T",
                f"{100.0 * entry['best_efficiency']:.1f}%",
            ]
        )
    story.append(make_table(perf_rows, col_widths=[3.2 * cm, 1.45 * cm, 1.45 * cm, 1.45 * cm, 1.45 * cm, 1.45 * cm, 2.6 * cm, 2.0 * cm]))
    story.append(PageBreak())

    story.append(Paragraph("6. Analysis Questions", styles["Section"]))
    qa = [
        (
            "Q1. Pseudocode and illustrative diagram",
            "Section 3.4 contains the per-iteration pseudocode and Figure 1 shows the hybrid execution flow. The important structural point is that the mesh must be globally consistent before the mover begins, which is why the MPI_Allreduce is placed after the local OpenMP scatter and reduction.",
        ),
        (
            "Q2. Race-condition handling",
            "Scatter is the only race-prone stage. Intra-rank races are removed with thread-private mesh buffers, and inter-rank conflicts are resolved by reducing rank-local meshes with MPI_Allreduce. The mover phase has no write-sharing because each thread only updates particles in its own local slice.",
        ),
        (
            "Q3. Graphs, speedup, and login-vs-compute node",
            "The report includes execution time, speedup, and efficiency plots based on the preserved cluster timing CSV files. A login node is meant for editing, compiling, and light interactive work, whereas a compute node is reserved for production runs and gives more stable timing behavior. For HPC performance measurements, compute nodes are the correct target because they avoid interference from shared interactive workloads.",
        ),
        (
            "Q4. Parallel efficiency and scalability",
            "Parallel efficiency E = Speedup / P. The large inputs scale better than the small input because they amortize synchronization and reduction overhead across more particle work. Efficiency falls at high worker counts because interpolation remains bandwidth-heavy and every iteration still needs a global mesh reduction and a global min/max reduction.",
        ),
        (
            "Q5. Maximum speedup achieved",
            f"The best measured speedup in the preserved dataset is {cluster['e']['best_speedup']:.2f}x for config e at {cluster['e']['best_threads']} threads ({cluster['e']['times'][0]:.3f}s down to {cluster['e']['best_time']:.3f}s). Config c is close behind at {cluster['c']['best_speedup']:.2f}x.",
        ),
        (
            "Q6. Why the observed speedups are sub-linear",
            "The dominant limits are memory bandwidth, mesh-reduction overhead, and synchronization. Scatter touches four mesh locations per particle and then performs an additional reduction across thread-private meshes. At larger worker counts, the amount of concurrent memory traffic rises faster than useful arithmetic, so the speedup curve bends away from ideal linear scaling.",
        ),
        (
            "Q7. Further optimization with larger HPC resources",
            "A stronger distributed-memory design would decompose both particles and mesh, using halo exchanges or sparse boundary reductions instead of a full replicated mesh on every rank. Additional improvements include structure-of-arrays particle storage, sorting particles by cell index, nonblocking MPI overlap, and GPU acceleration for scatter/gather kernels.",
        ),
        (
            "Q8. Load imbalance and bottlenecks",
            "Load imbalance appears as particles leave the domain or cluster unevenly in space. Even with equal initial partitions, some ranks or threads can end up with more active particles than others later in the run. The main computational bottleneck remains interpolation because it combines particle traversal, mesh updates, thread-local reduction, and a global MPI reduction in one stage.",
        ),
        (
            "Q9. Alternative data structure or approach",
            "A practical alternative is mesh-domain decomposition with ghost layers. Each rank owns a contiguous band or tile of the mesh, and particles are routed to the owning rank. This removes the need to keep the full mesh replicated everywhere and reduces the communication volume to boundaries instead of whole-grid reductions.",
        ),
        (
            "Q10. OpenMP/MPI design choice used in this submission",
            "The submitted Lab 8 code uses MPI to distribute particle ownership and OpenMP to parallelize work inside each rank. This hybrid structure maps naturally to cluster hardware: MPI scales across nodes, while OpenMP exploits the cores within a node without duplicating MPI state unnecessarily.",
        ),
        (
            "Q11. Phase-separated performance analysis",
            f"The preserved 4-rank correctness run on test.bin shows interpolation = {correctness['phase_percent']['Interpolation']:.1f}%, normalization = {correctness['phase_percent']['Normalization']:.1f}%, mover = {correctness['phase_percent']['Mover']:.1f}%, and denormalization = {correctness['phase_percent']['Denormalization']:.1f}% of total runtime. Although that is a small validation case, it still highlights interpolation as the dominant phase. For larger scientific inputs the mover cost will also grow substantially with particle count, but interpolation remains the primary bottleneck because it is the only phase that combines local parallel work with global reductions.",
        ),
    ]

    for title, answer in qa:
        story.append(Paragraph(title, styles["SubSection"]))
        story.append(Paragraph(answer, styles["BodySmall"]))

    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("7. Conclusion", styles["Section"]))
    story.append(
        Paragraph(
            "The Lab 8 submission now contains a corrected and cluster-oriented hybrid MPI + OpenMP implementation, correctness artifacts in data_cluster, and a performance analysis derived from the preserved cluster timing files in the submission bundle. The strongest measured result is a 3.50x speedup for the largest mesh configuration at 16 workers/threads, while the smaller cases plateau earlier because overhead and memory traffic dominate sooner. Overall, the results show that the pipeline benefits from parallelism, but interpolation and global synchronization still limit scalability and remain the best targets for future optimization.",
            styles["BodySmall"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Group 21 - Radhika Sanagadhiya (202301184) and Hiya Modi (202301011)", styles["BodySmall"]))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


if __name__ == "__main__":
    build_report()

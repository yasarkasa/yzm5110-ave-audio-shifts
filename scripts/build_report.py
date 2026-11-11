"""Build the YZM5110 report from saved results and the literature matrix."""

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
import matplotlib


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts/ttf"
pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("BodyBold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold")
INK = colors.HexColor("#162333")
MUTED = colors.HexColor("#4b5d70")
TEAL = colors.HexColor("#087b68")
STYLES = {
    "title": ParagraphStyle("title", fontName="BodyBold", fontSize=23, leading=29, spaceAfter=16, textColor=INK),
    "h1": ParagraphStyle("h1", fontName="BodyBold", fontSize=16, leading=21, spaceAfter=14, textColor=INK),
    "h2": ParagraphStyle("h2", fontName="BodyBold", fontSize=11, leading=16, spaceBefore=8, spaceAfter=7, textColor=INK),
    "body": ParagraphStyle("body", fontName="Body", fontSize=10.2, leading=14.9, spaceAfter=10, textColor=INK),
    "small": ParagraphStyle("small", fontName="Body", fontSize=8.4, leading=11.5, spaceAfter=7, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=8.3, leading=11.2, textColor=INK),
    "matrix": ParagraphStyle("matrix", fontName="Body", fontSize=8.2, leading=11.2, textColor=INK),
}


def p(text, style="body"):
    # Normalize dash characters to ASCII for portable PDF text rendering.
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    return Paragraph(text, STYLES[style])


def number(value, precision=2):
    return f"{value:.{precision}f}".replace("-0.00", "0.00")


def measured(value):
    return f"{number(value['estimate'])} [{number(value['ci95'][0])}, {number(value['ci95'][1])}]"


def table(rows, widths, style="cell"):
    values = [[p(escape(str(value)).replace("\n", "<br/>"), style) for value in row] for row in rows]
    tab = Table(values, colWidths=widths, hAlign="LEFT", repeatRows=1)
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0f5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, MUTED),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#d5dee6")),
    ]))
    return tab


def footer(canvas, doc):
    width, height = canvas._pagesize
    canvas.saveState()
    canvas.setFont("Body", 7.4)
    canvas.setFillColor(MUTED)
    canvas.drawString(46, height - 28, "Eren Kahraman  |  YZM5110  |  Audio shifts on AVE")
    canvas.drawString(46, 25, "Research project  |  11 November 2026")
    canvas.drawRightString(width - 46, 25, str(doc.page))
    canvas.restoreState()


def build(repo_url, published):
    test = json.loads((RESULTS / "ave_test.json").read_text())
    ref = json.loads((RESULTS / "ave_reference.json").read_text())
    lit = json.loads((ROOT / "report/literature.json").read_text())
    methods = ("reference", "local_average", "norm_matched")
    labels = {"reference": "A+V-att", "local_average": "Local averaging", "norm_matched": "Norm-matched"}
    destination = ROOT / "output/pdf/Kahraman_YZM5110_Research.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    title = "Audio Visual Event Localization under Temporal Audio Shifts on AVE"
    doc = BaseDocTemplate(str(destination), pagesize=A4, title=title, author="Eren Kahraman",
                          leftMargin=46, rightMargin=46, topMargin=49, bottomMargin=44)
    templates = []
    for name, size in (("portrait", A4), ("landscape", landscape(A4))):
        width, height = size
        frame = Frame(46, 44, width - 92, height - 96, leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        templates.append(PageTemplate(id=name, frames=[frame], pagesize=size, onPage=footer))
    doc.addPageTemplates(templates)
    story = []

    def prose(text):
        for paragraph in text.strip().split("\n\n"):
            story.append(p(paragraph.replace("\n", " ")))

    def page(heading):
        if story:
            story.append(PageBreak())
        story.append(p(heading, "h1"))

    story.append(p(title, "title"))
    story.append(p("Eren Kahraman<br/>Yildiz Technical University<br/>YZM5110 Multimodal Learning"
                   "<br/>Research project · 11 November 2026", "small"))
    story.append(p(f'<b>Public repository</b><br/><link href="{escape(repo_url)}" color="#087b68">'
                   f'{escape(repo_url)}</link>', "small"))
    if not published:
        story.append(p("Planned repository address. Public publication is pending.", "small"))
    story.append(p("Abstract", "h2"))
    prose("""This study measures the effect of audio-video clock errors on event localization with the published A+V-att model. Precomputed audio features are shifted by 0, ±1 and ±2 seconds. Each shift is compared with an unshifted control receiving exactly the same boundary mask. Model weights and original target labels are fixed.

On the original 402-clip AVE test split, a two-second shift reduces baseline accuracy by an average of 1.89 percentage points relative to matched controls (95% confidence interval [1.06, 2.74]). A single intervention, local audio averaging, improves shifted accuracy by 0.83 points over the baseline [0.29, 1.35]. Its reduction in the matched shift penalty is 0.58 points, with an interval including zero [-0.04, 1.18]. The experiment reports both the benefit under shifts and the cost on aligned inputs.""")
    story.append(p("1 Research question and scope", "h2"))
    prose("""The question is how well A+V-att recovers the original event class and timing when the audio stream arrives earlier or later than the video. A clock error tests the assumption that evidence from the two modalities is aligned at a shared timestamp.

The contributions are a critical comparison of five papers, reproduction of a published checkpoint on the original test split, a bidirectional shift protocol with matched boundary masks, local audio averaging with a norm-matched ablation, and uncertainty estimation at the source-video level. The scope is one checkpoint, one-second precomputed features and CPU inference. [1, 6]""")

    page("2 Literature search and critical synthesis")
    prose("""The initial search on 9 November 2026 used the queries “audio-visual event localization AVE temporal misalignment”, “temporal inconsistent audio-visual event localization” and “audio-visual event localization AVE cross-temporal alignment”. Publisher records, full texts and author repositories were consulted. Selection focused on five papers reporting AVE segment accuracy and representing different cross-modal interaction mechanisms. This is a focused project review.

Tian et al. use the audio at each second to weight visual regions. CMAN gates when and which modality to trust. PSP propagates features between useful pairs that need not be synchronous. CMBS suppresses irrelevant cross-modal evidence. AVSGN uses class-text semantics and cross-time subgraphs. [1-5]

Within-system ablations provide evidence for the respective components. Removing CMAN's sentinel changes accuracy from 77.1% to 76.1%. Removing PSP changes 77.8% to 73.7%. Removing CMBS temporal suppression changes 79.3% to 77.93%. Removing AVSGN's audio-visual subgraph changes 83.1% to 80.3%. These are published results. [2-5]""")
    story.append(table([["Study", "Published full / weak supervision", "Main mechanism"],
                        ["AVEL 2018", "72.7% / 66.7%", "Audio-guided visual attention"],
                        ["CMAN 2020", "77.1% / 75.7%", "Adaptive modality and time selection"],
                        ["PSP 2021", "77.8% / 73.5%", "Positive-pair feature propagation"],
                        ["CMBS 2022", "79.3% / 74.2%", "Temporal and event suppression"],
                        ["AVSGN 2025", "83.1% / 78.8%", "Text-supported semantic subgraphs"]], [105, 169, 229]))
    story.append(Spacer(1, 12))
    prose("""Cross-paper score differences also reflect encoders, training signals and implementation details. For example, AVSGN uses CLIP/CLAP features instead of Tian et al.'s VGG-based features. This project therefore measures controlled shifts and boundary losses within one fixed checkpoint. Appendix A covers all seven comparison fields required by the assignment.

Controlled shifting has prior examples, including the AV-AND repository. The present contribution is a limited experiment combining both directions, matched masks and paired uncertainty estimates for the selected weights. [10]""")

    page("3 Technical explanation of A+V-att")
    prose("""Each ten-second AVE clip is divided into ten one-second segments. A segment is assigned one of 28 event classes or background. The precomputed audio vector a(t) has 128 dimensions. Visual features V(t) contain a 512-dimensional vector at each position in a 7 × 7 spatial grid. [1, 6]

A+V-att applies linear transformations and ReLU to audio and visual features. The audio representation is broadcast across visual positions at the same second. Learned transformations and tanh produce spatial attention scores. A softmax over positions normalizes the scores, and their weighted sum summarizes the original visual vectors.

The attended visual sequence and the original audio sequence enter separate bidirectional LSTMs. Each direction has hidden size 128. The resulting 256-dimensional outputs are concatenated. ReLU, a 512-to-64 linear layer, ReLU, a 29-class linear layer and softmax produce segment probabilities. The largest probability determines the predicted class. [6]""")
    story.append(p("Visual attention and temporal context", "h2"))
    prose("""The visual summary is c(t) = sum_j alpha(t,j) V(t,j), where alpha(t,j) sums to one over spatial positions. The final decision p(y(t) | A,V) depends on both BiLSTMs and their context across the entire clip. Consequently, scoring only the central seconds does not remove the effect of missing boundary audio inside the model.

An audio shift can affect both the initial audio-guided visual attention and the temporal audio representation. This motivates the hypothesis. The reported accuracy measures their combined effect. Attention maps and hidden states were not causally disentangled.

The paper describes cross-entropy for supervised classification, while the inspected training script uses MultiLabelSoftMarginLoss. This discrepancy is recorded because the project evaluates an existing checkpoint. Reproducing training would require resolving this choice as a separate target. [1, 6]""")
    story.append(p("Connection to the course", "h2"))
    prose("""Week 3 connects fusion to controls for corrupted modalities. Week 4 motivates specifying the alignment unit and studying clock errors. Week 5 emphasizes grouping data by source families, motivating the additional source-video overlap analysis. [9]""")

    page("4 Reproduction target and implementation")
    prose("""The reproduction target is the 72.7% supervised A+V-att segment accuracy in Tian et al.'s Table 1 on the original AVE test split. With the published features and checkpoint, the expectation is agreement at the paper's one-decimal precision. A substantial discrepancy under verified inputs would require investigating data or implementation mismatches. [1]

The source and checkpoint are checked using SHA-256. A restricted loader accepts only expected legacy PyTorch classes. All checkpoint parameters are loaded into the modern network with strict=True. Four CUDA-specific zero states are created on the input device, and the legacy Xavier initializer is renamed. Learned parameters are retained. The checkpoint is model/AV_att.pt. [6]""")
    story.append(table([["Measurement", "Correct / total segments", "Accuracy"],
                       ["Published A+V-att", "Paper Table 1", "72.7%"],
                       ["This project, unmasked 0 s", "2,924 / 4,020", f"{number(ref['accuracy_percent'], 4)}%"]], [205, 180, 118]))
    story.append(Spacer(1, 12))
    prose("""The difference from the rounded published score is +0.0363 percentage points. Both values are 72.7% at one decimal. This reproduces inference with the released weights.

The original environment was Python 3.6 and PyTorch 0.3.0. This experiment used Python 3.12.14, PyTorch 2.15.0, NumPy 2.5.4 and h5py 3.16.0 on a macOS arm64 CPU. Accuracy inference used batches of 16 clips and four CPU threads.

The official audio download returned a Google Drive quota error, so the LECOO/AVE mirror with the expected shape and size was used. Visual features were read from the authors' HDF5 file using HTTP ranges that require matching 206 Content-Range headers and byte counts. Full-file identity between the audio mirror and the official file remains unverified. [7, 8]

An initial data-access attempt returned all-zero audio and was rejected. A later three-clip check verified finite, nonzero features and matching row-level labels, and the model produced outputs of shape (3,10,29). The reported experiments use this verified data path.""")
    story.append(p("Pinned upstream revision", "h2"))
    story.append(p("93f843fed72fb17394df76330df958b0c2dbde76", "small"))

    page("5 Proposed improvement and rationale")
    prose("""On validation, two-second shifts produced a net loss of 77 correct segments relative to matched controls. Losses were concentrated where the event-presence label differed between the audio source second and target second. Audio from after an event onset can make the model predict the event too early.

Before evaluating the intervention, one candidate was chosen. Each audio vector is blended with valid neighboring vectors within two seconds. The center receives 50% weight and the neighbor mean receives 50%. The center is excluded from that mean. Artificial boundary padding is excluded and remains zero. The center is retained when no valid neighbor exists. A zero center stays zero in both treatment and ablation.""")
    story.append(p("Local audio averaging", "h2"))
    prose("""Let N(t) contain valid neighbors s satisfying 0 &lt; |s-t| ≤ 2. Let m(t) be the mean of a(s) over N(t). The intervention is b(t) = 0.5 a(t) + 0.5 m(t). The processed input enters both the visual-attention and audio-LSTM paths of A+V-att.

The rationale is that nearby seconds can partly restore relevant audio around a displaced onset or offset. The method uses the provided validity mask and does not estimate shift direction or magnitude. Mixing neighbors can also blur transitions in correctly aligned inputs.""")
    story.append(p("Norm-matched ablation", "h2"))
    prose("""The ablation applies u(t) = a(t) ||b(t)||₂ / ||a(t)||₂. It retains the center vector's direction and matches the treatment's norm. This helps separate the contribution of neighboring feature directions from a change in magnitude. The target norm itself depends on neighbors, so the ablation also uses temporal context.

On validation, mean accuracy at ±2 seconds was 71.56% for the baseline, 72.16% for local averaging and 71.27% for the ablation. Unshifted accuracy changed from 73.42% to 73.34%. The radius and mixing weight were fixed before test evaluation. This single candidate and its unfavorable outcomes were retained.

Configuration and method-file hashes were recorded in the validation output. The test script stops if they differ. The test results therefore evaluate the same specified intervention.""")

    page("6 Experimental design and metrics")
    story.append(table([["Component", "Fixed protocol"],
                       ["Splits", "3,339 training / 402 validation / 402 original test clips"],
                       ["Inputs and target", "10 × 128 audio, 10 × 7 × 7 × 512 video; 29 original target classes"],
                       ["Offsets", "-2, -1, 0, +1, +2 seconds; positive offsets delay audio"],
                       ["Boundaries", "Zero padding without wraparound; identical zeros in the paired control"],
                       ["Scoring", "Indices 2-7 in every condition; 2,412 segments"],
                       ["Uncertainty", "10,000 source-video bootstrap replicates; seed 2026"],
                       ["Latency", "4 CPU threads; one clip; 5 warmups; first 32 clips per offset"]], [132, 371]))
    story.append(Spacer(1, 12))
    prose("""For offset k, shifted audio is a_k(t) = a(t-k). Out-of-clip values are zero. At +2 seconds, the first two audio segments are zero. The aligned control zeros exactly those same positions. At -2 seconds, both arms zero the last two segments. The BiLSTM observes all ten seconds, so matching is applied before inference.

The primary shift metric D₂ is the mean of control minus shifted accuracy across ±2 seconds. The hypothesis is D₂ &gt; 0, with secondary expectation D₂ &gt; D₁. The primary intervention contrast is local averaging minus baseline accuracy on shifted inputs, averaged across ±2 seconds. The same contrast is evaluated against the ablation. Aligned-input costs and each method's D₂ are reported separately.

Source video IDs are resampled jointly across all methods and offsets. The 2.5th and 97.5th percentiles define 95% intervals. Absolute accuracy and paired differences receive separate intervals. Per-offset intervals are unadjusted for multiple comparisons. The 402 test clips have distinct source IDs. Excluding eight IDs shared with training or validation yields a 394-clip sensitivity analysis.

Latency includes preprocessing, model execution and argmax from features already in memory. It excludes network access, disk access and raw feature extraction. Method order rotates across clips. Each arm has 160 observations, summarized by median and p95.""")

    page("7 Results and matched controls")
    story.append(p("Accuracy with shifted audio", "h2"))
    rows = [["Offset", "A+V-att", "Local averaging", "Norm-matched"]]
    for condition in test["conditions"]:
        line = [f"{condition['offset_seconds']:+d} s"]
        for method in methods:
            value = condition["methods"][method]
            bounds = value["accuracy_ci95_percent"]["shifted"]
            line.append(f"{number(value['accuracy_percent']['shifted'])}%\n[{number(bounds[0])}, {number(bounds[1])}]")
        rows.append(line)
    story.append(table(rows, [62, 147, 147, 147]))
    story.append(Spacer(1, 12))
    story.append(p("Mean shift penalty across directions", "h2"))
    rows = [["Method", "D₁ (percentage points)", "D₂ (percentage points)"]]
    for method in methods:
        rows.append([labels[method], measured(test["overall"][method]["d1_pp"]), measured(test["overall"][method]["d2_pp"])])
    story.append(table(rows, [145, 179, 179]))
    story.append(Spacer(1, 12))
    prose("""The baseline D₂ interval lies above zero, supporting the primary shift hypothesis. D₂ - D₁ is 1.49 [0.68, 2.34] percentage points. The two-second penalty is clearer than the mean one-second penalty. The forward and backward directions have different magnitudes.

At ±2 seconds, local averaging reaches 70.52%, the baseline 69.69% and the ablation 69.96%. Local averaging gains 0.83 [0.29, 1.35] points over the baseline and 0.56 [0.02, 1.10] over the ablation. The latter lower bound is close to zero. The reduction in the matched shift penalty is 0.58 [-0.04, 1.18] points. Evidence for improved shifted accuracy is stronger than evidence for a reduced shift penalty.""")

    page("7 Accuracy and paired differences")
    story.append(Image(str(RESULTS / "ave_test_accuracy.png"), width=503, height=398))
    story.append(p("Figure 1. Top, segment accuracy with shifted audio. Bottom, paired gains from local averaging against the baseline and ablation. Bars show source-video bootstrap 95% confidence intervals.", "small"))
    story.append(p("Aligned controls with matched boundary masks", "h2"))
    rows = [["Paired offset", "A+V-att (%)", "Local averaging (%)", "Norm-matched (%)"]]
    for condition in test["conditions"]:
        rows.append([f"{condition['offset_seconds']:+d} s", *[
            number(condition["methods"][m]["accuracy_percent"]["aligned"]) for m in methods]])
    story.append(table(rows, [122, 127, 127, 127]))
    story.append(Spacer(1, 10))
    prose("""Each offset masks a different boundary, so its aligned control has its own score. The +2 baseline is compared with its 71.89% control, and -2 with its 71.27% control. The 0-second value of 72.60% uses the central six seconds. The full-clip reproduction score is 72.7363%.""")

    page("7 Latency and failure analysis")
    rows = [["Method", "Median ms/clip", "p95 ms/clip", "Calls"]]
    for method in methods:
        value = test["latency"]["methods"][method]
        rows.append([labels[method], number(value["median_ms"], 3), number(value["p95_ms"], 3), value["samples"]])
    story.append(table(rows, [167, 124, 124, 88]))
    story.append(Spacer(1, 12))
    prose("""Local averaging adds about 0.020 ms/clip, or 2.9%, to the median in this run. These short CPU measurements are sensitive to machine load.

At ±2 seconds, event presence differs between source and target seconds in 508 of 4,824 segment-conditions (10.5%). This group accounts for 76 of the baseline's 91 net losses relative to matched controls (83.5%). Grouping uses the original temporal annotations.

Across the two directions, local averaging corrects 86 errors and introduces 46. In the event-presence mismatch group, these counts are 21 and 8. At zero shift, 27 errors are corrected and 29 correct segments are broken. The aligned-input difference is -0.08 [-0.70, 0.54] percentage points.""")
    story.append(table([["Example", "Target and baseline", "Local averaging"],
                       ["Row 27, +2 s, t=5. Bell at 5-10 s. Source audio t=3.", "Target bell. Baseline background.", "Bell. Onset recovered."],
                       ["Row 421, +2 s, t=2. Bark at 1-10 s. Source audio t=0.", "Target bark. Baseline bark.", "Background. New miss."],
                       ["Row 68, 0 s, t=6. Bell at 6-10 s.", "Target bell. Baseline bell.", "Background. Aligned onset blurred."]], [210, 155, 138]))
    story.append(Spacer(1, 12))
    prose("""Removing eight clips whose source IDs also occur in training or validation leaves 394 clips. The baseline has D₂ = 1.92 [1.10, 2.81] points. Local averaging gains 0.85 [0.32, 1.40] over the baseline and 0.57 [0.02, 1.12] over the ablation. The D₂ reduction remains uncertain at 0.59 [-0.04, 1.23] points. The main interpretation is similar after this filter.""")

    page("8 Limitations and conclusions")
    prose("""A two-second audio shift reduces A+V-att's ability to recover events on the original AVE timeline. Its matched-control D₂ interval is above zero. Local averaging improves shifted accuracy at a small measured latency cost. The interval for reduction of the shift penalty includes zero.

Labels remain on the original timeline. The experiment measures recovery under a sensor clock error. Relabeling the transformed input according to simultaneous audible-visible events would define a different target. This distinction bounds the interpretation.

The study uses one checkpoint and one dataset. One-second precomputed features obscure subsecond shifts and raw-encoder behavior. Synthetic padding and the validity mask are known to the experimental pipeline. Natural sensor delays may behave differently. The method is offline, using future neighbors and a bidirectional baseline.

Full identity of the audio mirror to the official file remains unverified. Source-video overlap was tested, but overlap with pretraining data was not measured. Bootstrap intervals concern test-sample uncertainty and do not cover retraining or checkpoint variability. Latency covers inference from precomputed features.

Open questions include subsecond and variable delays, natural inconsistency, other checkpoints, and neighborhood mixing that better preserves event boundaries. These require a new validation design. The method was not tuned using the final test results.""")
    story.append(p("AI assistance disclosure", "h2"))
    prose("""OpenAI Codex assisted with source search, the comparison matrix and synthesis draft, CPU adaptation of the authors' implementation, data checks, experiment scripts and local execution, bootstrap and failure analysis, figures, and report/presentation editing. The topic, hypothesis, matched controls and local averaging/ablation design were developed during the conversation with Codex suggestions. Numerical results come from saved local script outputs.

Section 7 of the assignment permits disclosed assistance. Eren Kahraman remains responsible for reading sources, understanding the implementation, assessing the experimental design, checking claims and citations, and defending the conclusions. Specific contributions are documented in AI_USAGE.md.""")

    story.append(NextPageTemplate("landscape"))
    page("Appendix A  Comparison of five papers")
    story.append(p("A1  Question and contribution, modalities and assumptions, mechanism and objective. Published findings are distinguished from this project's measurements.", "small"))
    story.append(table([["Paper", "Question and contribution", "Modalities and assumptions", "Mechanism and objective"], *[
        [item["name"], item["question"], item["modalities"], item["mechanism"]] for item in lit]],
        [100, 218, 204, 228], "matrix"))

    page("Appendix A  Data and supporting evidence")
    story.append(p("A2  Continuation of the same five rows, covering all seven required comparison fields. Full-text sources [1-5].", "small"))
    story.append(table([["Paper", "Data and protocol", "Baselines and evidence", "Resources and reproducibility", "Limitations and connections"], *[
        [item["name"], item["data"], item["evidence"], item["resources"], item["limits"]] for item in lit]],
        [92, 163, 170, 162, 163], "matrix"))

    story.append(NextPageTemplate("portrait"))
    page("References and reproduction record")
    refs = [
        ("[1] Tian, Y., Shi, J., Li, B., Duan, Z. and Xu, C. (2018). Audio-Visual Event Localization in Unconstrained Videos. ECCV.", lit[0]["url"]),
        ("[2] Xuan, H., Zhang, Z., Chen, S., Yang, J. and Yan, Y. (2020). Cross-Modal Attention Network for Temporal Inconsistent Audio-Visual Event Localization. AAAI.", lit[1]["url"]),
        ("[3] Zhou, J., Zheng, L., Zhong, Y., Hao, S. and Wang, M. (2021). Positive Sample Propagation Along the Audio-Visual Event Line. CVPR.", lit[2]["url"]),
        ("[4] Xia and Zhao (2022). Cross-Modal Background Suppression for Audio-Visual Event Localization. CVPR.", lit[3]["url"]),
        ("[5] Liu et al. (2025). Audio-Visual Semantic Graph Network for Audio-Visual Event Localization. CVPR.", lit[4]["url"]),
        ("[6] Tian et al. AVE-ECCV18 source code and checkpoint. Revision 93f843fed72fb17394df76330df958b0c2dbde76.", "https://github.com/YapengTian/AVE-ECCV18"),
        ("[7] Authors' links to AVE audio and visual features.", "https://github.com/YapengTian/AVE-ECCV18#ave-dataset--features"),
        ("[8] LECOO/AVE audio feature mirror. Accessed 10 November 2026.", "https://huggingface.co/datasets/LECOO/AVE/tree/main"),
        ("[9] Cetinkaya, E. YZM5110 Multimodal Learning, Weeks 1-5 slides and Research Project instructions. 2026. Course materials supplied by the student.", None),
        ("[10] AV-AND repository. Controlled temporal misalignment examples.", "https://github.com/cataug/AV-AND#temporal-misalignment"),
    ]
    for description, url in refs:
        value = escape(description)
        if url:
            value += f' <link href="{escape(url)}" color="#087b68">Source</link>'
        story.append(p(value, "small"))
    story.append(p("Runnable submission", "h2"))
    prose("""The repository contains code, fixed configurations, JSON/CSV outputs, commands and the AI disclosure. The English submission is pinned by the commit linked in the project handoff and GitHub history. A GitHub Release is optional. README.md lists exact execution commands. scripts/export_tables.py produces the tables and scripts/plot_ave_test.py produces the figure.

Experiments conducted on 9-10 November were packaged on 11 November. Separate commits were not recorded during the experiments. The project log preserves their stage records. Upstream code, course PDFs and feature files are obtained separately rather than redistributed here.""")
    story.append(p("Configuration SHA-256", "h2"))
    digest = test["config_sha256"]
    story.append(p(digest[:32] + "<br/>" + digest[32:], "small"))
    doc.build(story)
    print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--published", action="store_true", help="The named repository has been published and verified")
    args = parser.parse_args()
    build(args.repo_url, args.published)

# Attribution and reused components

## A+V-att implementation

The project uses Yapeng Tian et al.'s [AVE-ECCV18 repository](https://github.com/YapengTian/AVE-ECCV18) at revision 93f843fed72fb17394df76330df958b0c2dbde76. The AV_att.pt checkpoint, models.py, original split lists and labels are obtained from that checkout. These upstream assets are not redistributed here. No separate LICENSE file was found in the inspected revision. Users should verify the original code, model and data terms with the source owners.

The loader in scripts/ave_smoke.py checks file hashes and restricts accepted legacy object classes. When the pinned models.py is executed in memory, four CUDA-specific zero states are made device-aware and the old Xavier initializer name is updated. All learned parameters are loaded from the published checkpoint. The training-loss discrepancy between the paper and upstream training script is recorded. This project evaluates checkpoint inference.

Citation, Tian, Y., Shi, J., Li, B., Duan, Z. and Xu, C. (2018). *Audio-Visual Event Localization in Unconstrained Videos*. ECCV. [Paper](https://arxiv.org/abs/1803.08842).

## AVE features

Visual features are read from the authors' HDF5 link through HTTP byte ranges. Audio uses the [LECOO/AVE mirror](https://huggingface.co/datasets/LECOO/AVE/tree/main) because the official Google Drive link returned a quota error. The mirror's SHA-256 is 6765e445a5a66853282964576222c7aaf895b563100b2d99f29ecfd413c7d8fc. This identifies the audio version used. Full-file identity with the official audio asset remains unverified.

Raw videos, feature files and large checkpoints are excluded from Git. Public availability of a download link does not establish redistribution rights. Access and use are subject to the authors' and providers' conditions. The preparation command assumes the reader has assessed those conditions for their intended use.

## Course materials

Ekrem Cetinkaya's YZM5110 slides and project instructions were reviewed in the local kaynaklar/ directory. Course PDFs are excluded from the public repository. Week 4 temporal alignment and Week 5 source-family splits informed the experiment. Project-specific code, outputs, reports and slides remain subject to the individual-work policy.

## Software

Inference used Python 3.12.14, NumPy 2.5.4, h5py 3.16.0 and PyTorch 2.15.0. Figures use Matplotlib 3.10.8, the report uses ReportLab and the editable presentation was authored with OpenAI Artifact Tool. Each software package retains its own license. AI contributions are disclosed in [AI_USAGE.md](AI_USAGE.md).

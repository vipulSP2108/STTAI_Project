# Building the two reports
Place this folder at `report/` in the repo (figures_v2/ beside it). Then:
    cd report
    for r in report_A1 report_A2; do pdflatex $r && bibtex $r && pdflatex $r && pdflatex $r; done
Needs TeX Live with acmart, libertine, newtx, inconsolata (texlive-publishers, -fonts-extra, -latex-extra).
Regenerate figures from the repo root:  python code/scripts/make_report_figures.py . report/figures_v2   (then copy fig_*.pdf next to the .tex)

## Update after you re-run things
* numbers.tex  - every metric / kappa / latency lives here. Red [TBD: ...] boxes MUST be replaced.
* tab_runs/tab_err/tab_slices/tab_dis.tex are auto-generated from result files (rebuild when results change).
* Insert screenshots under report/shots/ (names are printed in red where missing):
  labelstudio_task.png, dvc_status.png, validation_run.png, ui_prediction.png, mlflow_runs.png, docker_validate.png, ci_green.png

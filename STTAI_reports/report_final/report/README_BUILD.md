# Build the reports
Put this folder at `report/` in the repo, then:
    cd report
    for r in report_A1 report_A2; do pdflatex $r && bibtex $r && pdflatex $r && pdflatex $r; done
Needs TeX Live: acmart, libertine, newtx, inconsolata (texlive-publishers, -fonts-extra, -latex-extra, -plain-generic).
Regenerate figures (repo root):
    python code/scripts/make_report_figures.py . report/figures_v2          # pilot / deployment figures
    python code/scripts/make_report_figures_final.py . report/figures_v3    # final corpus + model figures
then copy fig_*.pdf and tab_*.tex next to the .tex files.
Screenshots: place under report/shots/ (filenames shown in red where missing).

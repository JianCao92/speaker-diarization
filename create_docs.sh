#!/bin/sh
# Creates/updates `README.{html/pdf}` from README.md
# Requires `pandoc` and `latex`

pandoc README.md -f markdown -t html -s -o README.html
pandoc README.md -f markdown -s -o README.pdf

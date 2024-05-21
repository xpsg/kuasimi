#!/bin/bash
export GEMINI_API_KEY=
grim -g "$(slurp -b 1e1e1ecc -c 78aeed)" /tmp/screenshot.png
python ./kuasimi.py -f /tmp/screenshot.png
rm /tmp/screenshot.png

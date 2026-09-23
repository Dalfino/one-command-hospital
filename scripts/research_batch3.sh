#!/bin/bash
# Deep research batch 3: gap-filling
cd /home/z/my-project/research

z-ai function -n web_search -a '{"query": "open source clinical AI hospital vs commercial Nuance DAX Abridge Epic procurement cost comparison", "num": 8}' -o commercial.json
z-ai function -n web_search -a '{"query": "MedGemma license Gemma terms of use commercial hospital fine-tuning restrictions", "num": 6}' -o medgemma-license.json
z-ai function -n web_search -a '{"query": "hospital AI governance committee clinical AI deployment oversight validation workflow", "num": 6}' -o governance.json

echo "BATCH3 DONE"

#!/bin/bash
# Deep research batch 1: the 8 open-source medical AI projects
mkdir -p /home/z/my-project/research
cd /home/z/my-project/research

z-ai function -n web_search -a '{"query": "Google MedGemma medical multimodal LLM MedQA benchmarks multimodal chest X-ray pathology capabilities", "num": 8}' -o medgemma.json
z-ai function -n web_search -a '{"query": "MedGemma 4B 27B model card clinical applications hospital deployment license", "num": 8}' -o medgemma2.json
z-ai function -n web_search -a '{"query": "BioMistral 7B open source medical LLM PubMed Central pretraining benchmark performance license", "num": 8}' -o biomistral.json
z-ai function -n web_search -a '{"query": "Meditron EPFL clinical large language model 70B fully open audited training corpus low-resource", "num": 8}' -o meditron.json
z-ai function -n web_search -a '{"query": "Microsoft BioGPT biomedical text generation relation extraction PubMedQA performance license", "num": 8}' -o biogpt.json
z-ai function -n web_search -a '{"query": "medspaCy clinical NLP toolkit ConText negation section detection tempovacy clinical notes", "num": 8}' -o medspacy.json
z-ai function -n web_search -a '{"query": "scispaCy AllenAI biomedical NER UMLS entity linking models en_ner_bc5cdr", "num": 8}' -o scispacy.json
z-ai function -n web_search -a '{"query": "OpenBioLLM Llama3 8B biomedical LLM medical benchmarks GPT-4 level performance", "num": 8}' -o openbiollm.json
z-ai function -n web_search -a '{"query": "Clinical-Longformer Clinical-T5 Stanford AIMI MIMIC-III clinical text encoder pretrained", "num": 8}' -o clinical-t5.json
z-ai function -n web_search -a '{"query": "Clinical-T5 Clinical-Longformer readmission prediction sepsis EHR notes fine-tuning applications", "num": 8}' -o clinical-t5-apps.json

echo "BATCH1 DONE"
ls -la /home/z/my-project/research/

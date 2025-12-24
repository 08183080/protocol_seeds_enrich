# ProSeedsBench

[English](README_en.md) | 中文

## Background
Network protocol fuzzing can be categorized into generation-based and mutation-based approaches. Generation-based network protocol fuzzing is time-consuming and error-prone, making mutation-based approaches more preferred. However, a major challenge for mutation-based network protocol fuzzing is its dependence on initial seeds. This tool is a module of the XPGFUZZ sub-tool, designed to enhance initial seeds using LLM, providing a rich initial seed corpus. Additionally, this work proposes a benchmark for initial seed enrichment in network protocol fuzzing, which can be used in combination with profuzzbench.


## Directory Structure
```
ProSeedsBench/
├── data/               # Protocol knowledge base data
│   ├── codes/          # Protocol code files
│   │   ├── DAAP/
│   │   ├── FTP/
│   │   ├── HTTP/
│   │   ├── RTSP/
│   │   ├── SIP/
│   │   ├── SMTP/
│   │   └── README.md
│   ├── cves/           # CVE vulnerability information
│   │   ├── FTP/
│   │   ├── HTTP/
│   │   ├── RTSP/
│   │   ├── SIP/
│   │   ├── SMTP/
│   │   ├── get_cves.py
│   │   └── README.MD
│   ├── deepwikis/      # Protocol deep knowledge base
│   │   ├── DAAP/
│   │   ├── FTP/
│   │   ├── HTTP/
│   │   ├── RTSP/
│   │   ├── SIP/
│   │   ├── SMTP/
│   │   └── README.md
│   ├── rfcs/           # RFC documents
│   │   ├── FTP/
│   │   ├── HTTP/
│   │   ├── RTSP/
│   │   ├── SIP/
│   │   ├── SMTP/
│   │   └── README.md
│   └── README.md
├── docs/               # Project documentation
│   ├── Implementation_Roadmap.md
│   ├── LLM_Enrichment_Strategy.md
│   └── README.MD
├── papers/             # Related papers
│   └── README.md
├── seeds/              # Protocol seed files
│   ├── DAAP/
│   ├── FTP/
│   ├── HTTP/
│   ├── RTSP/
│   ├── SIP/
│   ├── SMTP/
│   └── README.MD
├── protocols.xlsx      # Protocol information table
├── README.md           # Project documentation (Chinese)
└── README_en.md        # Project documentation (English)
```

## Changelog
- [x] 12/1, Started constructing a protocol knowledge base and exploring methods to maximize its utilization. Initially focusing on all text protocols in profuzzbench as a pilot.
- [x] 12/7, Collected all CVEs for benchmark text protocols in recent years. Continuously improving the protocol knowledge base.
- [x] 12/7, Extracted main code files for aggregated protocols.
- [x] 12/24, Came up with a big idea: creating a benchmark tool that implements all seed enrichment strategies from various network protocol fuzzing approaches in one framework with adjustable parameters. Also proposing metrics to evaluate seed quality. This is thorough, interesting, and belongs to knowledge engineering. Let's begin.



## Protocol Knowledge Base Construction and Utilization
To do...



## Seed Enrichment Method Reproduction and Enhancement
- [ ] Reproduce ChatAFL's seed enrichment method

# Contact
Email: pxxhl@qq.com


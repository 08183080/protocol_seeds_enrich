# protocol_seeds_enrich

[English](README.md) | 中文

## 背景
网络协议模糊测试有基于生成的和基于变异的两种类型。基于生成的网络协议模糊测试耗时且容易出错，因此现在更倾向于基于变异的网络协议模糊测试。而基于变异的网络协议模糊测试的一大挑战就是对于初始种子的依赖。因此本工具，是XPGFUZZ子工具的一个模块，旨在利用LLM增强初始种子。为大家提供一个丰富的初始种子预料库。同时，本文提出一个网络协议模糊测试的初始种子丰富的基准集，可以和profuzzbench配套组合使用。


## 目录结构
```
ProSeedsBench/
├── codes/              # 协议代码文件
│   ├── DAAP/
│   ├── FTP/
│   ├── HTTP/
│   ├── RTSP/
│   ├── SIP/
│   ├── SMTP/
│   └── README.md
├── cves/               # CVE漏洞信息
│   ├── FTP/
│   ├── HTTP/
│   ├── RTSP/
│   ├── SIP/
│   ├── SMTP/
│   ├── get_cves.py
│   └── README.MD
├── deepwikis/          # 协议深度知识库
│   ├── DAAP/
│   ├── FTP/
│   ├── HTTP/
│   ├── RTSP/
│   ├── SIP/
│   ├── SMTP/
│   └── README.md
├── docs/               # 项目文档
│   ├── Implementation_Roadmap.md
│   └── LLM_Enrichment_Strategy.md
├── papers/             # 相关论文
├── rfcs/               # RFC文档
│   ├── FTP/
│   ├── HTTP/
│   ├── RTSP/
│   ├── SIP/
│   ├── SMTP/
│   └── README.md
├── seeds/              # 协议种子文件
│   ├── DAAP/
│   ├── FTP/
│   ├── HTTP/
│   ├── RTSP/
│   ├── SIP/
│   └── SMTP/
├── protocols.xlsx      # 协议信息表格
└── README.md           # 项目说明文档
```

## 日志
- [x] 12/1，我想要构造一个协议知识库，并探索最大化利用它信息的方法。首先以profuzzbench中更多所有文本协议为试点。
- [x] 12/7，获取bench文本协议的近年以来的所有的cve。不断完善协议的知识库ing。
- [x] 12/7，提取聚合协议的的一些主要代码文件。
- [x] 12/24，产生一个很大的想法：我觉得可以做一个基准工具，把目前的所有家的网络协议模糊测试的种子丰富策略全都实现在这一个框架中，参数可以调节。并提出一种评估各种种子的质量的指标。我觉得这样极致彻底，也很有趣。这是属于知识工程了。开始吧。



## 协议知识库的构建和利用
To do...



## 种子丰富方法的复现和增强
- [ ] 复现chatafl的种子丰富方法

# 交流
邮箱：pxxhl@qq.com
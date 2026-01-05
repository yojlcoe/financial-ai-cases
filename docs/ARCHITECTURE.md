# システムアーキテクチャ仕様書

## 概要

事例調査AIエージェントは、金融機関のAI・DX事例を自動収集・分析するシステムです。

**最終更新日:** 2025-12-30

---

## システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                    (Next.js + React)                        │
│                                                             │
│  - 企業管理UI                                                │
│  - 記事閲覧UI                                                │
│  - ジョブ実行UI                                              │
│  - 検索設定UI ← 新規追加                                      │
│  - レポート生成UI                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                       Backend                               │
│                  (FastAPI + Python)                         │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  API Layer  │  │   Services   │  │  Repositories   │   │
│  │             │  │              │  │                 │   │
│  │ - Companies │  │ - Crawler    │  │ - Company Repo  │   │
│  │ - Articles  │  │ - LLM Filter │  │ - Article Repo  │   │
│  │ - Jobs      │  │ - Scheduler  │  │ - Settings Repo │   │
│  │ - Settings  │  │ - Reporter   │  │                 │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQLAlchemy ORM (async)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    PostgreSQL                               │
│                                                             │
│  - companies                                                │
│  - source_urls                                              │
│  - articles                                                 │
│  - job_histories                                            │
│  - schedule_settings (スケジュール)                          │
│  - global_search_settings (検索キーワード・LLM)              │
│  - company_search_settings (企業別設定)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    External Services                        │
│                                                             │
│  - DuckDuckGo Search API                                    │
│  - Ollama (LLM: llama3.2:1b)                                │
│  - BeautifulSoup (Webスクレイピング)                         │
└─────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 2.0
**Last Updated:** 2025-12-30
**Author:** AI Case Study Research System Team

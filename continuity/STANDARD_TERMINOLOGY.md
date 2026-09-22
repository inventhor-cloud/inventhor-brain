# Standard Software Terminology

Use these names consistently in code, files, UI and handoff documents so a new AI/provider can search and understand the system quickly.

| INVENTHOR concept | Standard software term |
|---|---|
| Ana gerçek kayıt | System of Record (SoR) / Source of Truth |
| Proje listesi | Project Registry |
| Yapılacak işler | Backlog / Work Item Backlog |
| Sıradaki işler | Ready Queue / Work Queue |
| Çalışan işler | In-Flight Work |
| Biten işler | Completed Work |
| Fikir havuzu | Idea Backlog |
| Yapılan değişiklik geçmişi | Event Log / Audit Log |
| Kaldığı yer | Checkpoint |
| Yeni yapay zekaya devir | Handoff Packet |
| Mimari karar | Architecture Decision Record (ADR) |
| Çıktı/paket | Artifact |
| Çıktı deposu | Artifact Registry |
| Kanıt | Evidence |
| Kanıt deposu | Evidence Store |
| Proje bilgisi | Project State |
| Bilgi tabanı | Knowledge Base |
| Yerel kopya | Local Cache / Replica |
| Bulut eşitleme | Replication / Sync |
| Çakışma çözümü | Conflict Resolution |
| Sürüm | Version / Revision |
| Çalıştırma kaydı | Run Record |
| Kurtarma noktası | Snapshot / Checkpoint |

## Canonical naming rules

- INVENTHOR Main owns the System of Record.
- Windows Operator keeps a Local Replica for resilience and execution.
- Cloud storage holds an encrypted/synchronized replica, not a second independent truth.
- A provider chat is never the System of Record.
- Handoff Packets are compact and provider-neutral.
- Architecture Decision Records explain why major decisions were made.
- Event Log records state transitions; it is append-oriented.

# Arquitetura

```text
Supabase Storage (CSV privado)
          │ download autenticado
          ▼
DataSourceService ── SHA-256 ── CSV local temporário
          │
          ▼
Parquet ZSTD (cache analítico)
          │
          ├── AnalyticsService: prevalências, Wilson, RP, Poisson robusto
          ├── MapService: agregação por escola + Folium
          └── Django Views: Tabelas | Dashboards | Mapa | API JSON
```

A fonte permanece simples e auditável. O Parquet reduz tempo de leitura e uso de memória. O hash impede conversões desnecessárias. Resultados agregados são cacheados por versão da fonte.

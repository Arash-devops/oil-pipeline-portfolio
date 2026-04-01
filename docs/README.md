# Documentation Index

This directory contains the architecture documentation and diagram sources for the Oil Price Data Pipeline project.

---

## Documents

| File | Description |
|------|-------------|
| [`architecture.md`](architecture.md) | Deep-dive technical architecture: system context, container diagram, data model, API layer, monitoring, CI/CD, deployment, security |

---

## Diagrams

All diagrams are available as Mermaid source (`.mmd`) and PNG export.

| Diagram | Source | PNG | Description |
|---------|--------|-----|-------------|
| Pipeline Overview | [pipeline-overview.mmd](diagrams/pipeline-overview.mmd) | [PNG](diagrams/pipeline-overview.png) | End-to-end data flow from Yahoo Finance to the portfolio website |
| Docker Topology | [docker-topology.mmd](diagrams/docker-topology.mmd) | [PNG](diagrams/docker-topology.png) | Docker Compose service dependencies, volumes, and ports |
| Data Warehouse Schema | [data-warehouse-schema.mmd](diagrams/data-warehouse-schema.mmd) | [PNG](diagrams/data-warehouse-schema.png) | Star schema ER diagram with staging table |
| Medallion Architecture | [medallion-architecture.mmd](diagrams/medallion-architecture.mmd) | [PNG](diagrams/medallion-architecture.png) | Bronze → Silver → Gold data flow with transformation steps |
| CI/CD Pipeline | [cicd-pipeline.mmd](diagrams/cicd-pipeline.mmd) | [PNG](diagrams/cicd-pipeline.png) | GitHub Actions workflow jobs and dependencies |
| Monitoring Stack | [monitoring-stack.mmd](diagrams/monitoring-stack.mmd) | [PNG](diagrams/monitoring-stack.png) | Prometheus + Grafana metrics collection and visualisation |

---

## Regenerating PNGs

If you modify a `.mmd` file, regenerate its PNG with:

```bash
# Single diagram
npx @mermaid-js/mermaid-cli -i docs/diagrams/pipeline-overview.mmd \
  -o docs/diagrams/pipeline-overview.png \
  -t dark -b transparent -w 2048 \
  -p puppeteer-config.json

# All diagrams at once
for f in docs/diagrams/*.mmd; do
  npx @mermaid-js/mermaid-cli \
    -i "$f" \
    -o "${f%.mmd}.png" \
    -t dark -b transparent -w 2048 \
    -p puppeteer-config.json
done
```

The `puppeteer-config.json` at the project root contains `{ "args": ["--no-sandbox"] }` which is required on Linux CI environments.

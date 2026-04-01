export type PipelineStage = {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  description: string;
  techStack: string[];
  highlights: string[];
  diagramKey?: string;
  category: 'data' | 'infrastructure' | 'api' | 'frontend';
  accentColor: string;
};

export const pipelineStages: PipelineStage[] = [
  {
    id: 'schema-design',
    number: 1,
    title: 'Schema Design',
    subtitle: 'Star Schema & Dimensional Modelling',
    description:
      'Designed a dimensional data warehouse using a Star Schema with one central fact table and three dimension tables. Followed Kimball methodology: surrogate integer keys, SCD Type 2 for slowly changing commodity attributes, and a date dimension pre-populated with 10+ years of calendar data.',
    techStack: ['PostgreSQL', 'SQL', 'Star Schema'],
    highlights: [
      'dim_date with ISO weekday, quarter, fiscal-year columns',
      'dim_commodity with SCD Type 2 (valid_from / valid_to)',
      'UNIQUE constraint on (date_key, commodity_key, source_key)',
    ],
    diagramKey: 'data-warehouse-schema',
    category: 'data',
    accentColor: '#34d399',
  },
  {
    id: 'database-impl',
    number: 2,
    title: 'Database Implementation',
    subtitle: 'DDL, Stored Procedures & Staging',
    description:
      'Implemented the full PostgreSQL schema across four init scripts: dimension tables, fact table, staging table, and stored procedures. The sp_process_staging() procedure validates and promotes rows from staging to the warehouse using INSERT … ON CONFLICT DO NOTHING for idempotency.',
    techStack: ['PostgreSQL', 'PL/pgSQL', 'psycopg v3'],
    highlights: [
      'Four sequential init SQL scripts (00–04)',
      'sp_process_staging() stored procedure',
      'Staging table with is_valid flag and validation_errors column',
    ],
    category: 'data',
    accentColor: '#34d399',
  },
  {
    id: 'ingestor',
    number: 3,
    title: 'Data Ingestor',
    subtitle: 'Yahoo Finance → PostgreSQL',
    description:
      'Built a Python batch service that fetches OHLCV price data for four energy commodities from Yahoo Finance, validates every row, batch-inserts into staging, then calls the stored procedure to promote to the warehouse. Supports backfill, incremental, and refresh modes.',
    techStack: ['Python', 'yfinance', 'psycopg v3', 'tenacity'],
    highlights: [
      'ConnectionPool (min 2, max 10) via psycopg-pool',
      'Exponential backoff retries with tenacity',
      'Per-symbol ASCII summary table on exit',
    ],
    category: 'data',
    accentColor: '#38bdf8',
  },
  {
    id: 'validation',
    number: 4,
    title: 'Validation & Quality',
    subtitle: 'Row-level Guards & Idempotency',
    description:
      'Every inbound row is validated before staging insert: non-null symbol and close price, price_close > 0, price_high >= price_low, trade_date not in the future, and trade_date not a weekend. Invalid rows are marked is_valid = FALSE with a semicolon-separated validation_errors string rather than being dropped.',
    techStack: ['Python', 'PostgreSQL', 'PL/pgSQL'],
    highlights: [
      '6 validation rules per row',
      'Failed rows retained with reason codes',
      'Idempotent upsert via ON CONFLICT DO NOTHING',
    ],
    category: 'data',
    accentColor: '#38bdf8',
  },
  {
    id: 'lakehouse',
    number: 5,
    title: 'Medallion Lakehouse',
    subtitle: 'Bronze → Silver → Gold Parquet',
    description:
      'Transforms the PostgreSQL warehouse into a three-layer Parquet lakehouse. Bronze is a Hive-partitioned exact copy. Silver applies null-filling, type coercion, and quality reports. Gold produces three flat analytical datasets (monthly_summary, price_metrics, commodity_comparison) consumed by the API.',
    techStack: ['DuckDB', 'PyArrow', 'Parquet', 'Python'],
    highlights: [
      'Hive partitioning by symbol/year/month',
      'Per-partition quality reports in Silver',
      '3 Gold datasets: monthly, metrics, comparison',
    ],
    diagramKey: 'medallion-architecture',
    category: 'data',
    accentColor: '#34d399',
  },
  {
    id: 'api',
    number: 6,
    title: 'REST API',
    subtitle: 'FastAPI Dual-Backend',
    description:
      'FastAPI service exposing 8 REST endpoints over two backends: async psycopg v3 pool for operational PostgreSQL queries, and per-request DuckDB connections for Gold-layer Parquet analytics. Returns a standard { status, data, meta } JSON envelope with structured logging via structlog.',
    techStack: ['FastAPI', 'psycopg v3', 'DuckDB', 'Pydantic v2', 'structlog'],
    highlights: [
      'AsyncConnectionPool for PostgreSQL',
      'Thread-pool DuckDB for analytics endpoints',
      'Prometheus MetricsMiddleware at /metrics',
    ],
    category: 'api',
    accentColor: '#818cf8',
  },
  {
    id: 'docker',
    number: 7,
    title: 'Docker',
    subtitle: 'Multi-Service Containerization',
    description:
      'Containerized all six services (postgres, ingestor, lakehouse, api, prometheus, grafana) using Docker Compose. Each Python service uses python:3.13-slim with libpq5 at runtime. Named volumes share Parquet data between the lakehouse writer and API reader.',
    techStack: ['Docker', 'Docker Compose', 'python:3.13-slim'],
    highlights: [
      'Shared lakehouse-data volume (RW → RO)',
      'Health checks for postgres dependency',
      'One command: docker compose up',
    ],
    diagramKey: 'docker-topology',
    category: 'infrastructure',
    accentColor: '#38bdf8',
  },
  {
    id: 'kubernetes',
    number: 8,
    title: 'Kubernetes & Helm',
    subtitle: 'Production-Grade Orchestration',
    description:
      'Wrote 29 Kubernetes manifests covering Deployments, Jobs, Services, PersistentVolumeClaims, ConfigMaps, Secrets, ServiceMonitor, and HPA. Packaged into a Helm chart with environment-specific values, _helpers.tpl templating, and conditional feature flags.',
    techStack: ['Kubernetes', 'Helm', 'YAML'],
    highlights: [
      'RollingUpdate strategy with readiness probes',
      'Init containers for PostgreSQL readiness',
      'HPA on API Deployment (cpu: 70%)',
    ],
    category: 'infrastructure',
    accentColor: '#818cf8',
  },
  {
    id: 'cicd',
    number: 9,
    title: 'CI/CD',
    subtitle: 'GitHub Actions Pipeline',
    description:
      'Six-job GitHub Actions pipeline: matrix linting (ruff check + format) across all Python services, ESLint for the frontend, pytest for the API, docker build validation (no push), and GitHub Pages deployment. The API test suite has 48 tests across 5 modules.',
    techStack: ['GitHub Actions', 'ruff', 'pytest', 'Docker'],
    highlights: [
      '48 API tests: mocked PostgreSQL, real DuckDB',
      'Matrix builds for 3 Python services',
      'GHA layer cache for Docker builds',
    ],
    diagramKey: 'cicd-pipeline',
    category: 'infrastructure',
    accentColor: '#fbbf24',
  },
  {
    id: 'monitoring',
    number: 10,
    title: 'Monitoring',
    subtitle: 'Prometheus + Grafana',
    description:
      'Added a MetricsMiddleware to the FastAPI app that records five Prometheus metrics per request. Grafana is auto-provisioned with a datasource and a 10-panel dashboard covering request rate, error rate, P95 latency, DB query duration, and process metrics.',
    techStack: ['Prometheus', 'Grafana', 'prometheus-client'],
    highlights: [
      '5 metrics: Counter, Histogram, Gauge',
      '10-panel Grafana dashboard (auto-provisioned)',
      'track_db_query async context manager',
    ],
    diagramKey: 'monitoring-stack',
    category: 'infrastructure',
    accentColor: '#fb7185',
  },
  {
    id: 'documentation',
    number: 11,
    title: 'Documentation',
    subtitle: '6 Diagrams · 1,755 Lines',
    description:
      'Comprehensive documentation covering architecture, data model, API reference, CI/CD, monitoring, and deployment. Six Mermaid diagrams exported as PNGs, a 600-line root README with recruiter-friendly narrative, a 413-line deep technical architecture doc, and per-service READMEs.',
    techStack: ['Mermaid', 'Markdown', 'mermaid-cli'],
    highlights: [
      '6 architecture diagrams (PNG exported)',
      '600-line root README',
      'docs/architecture.md: system context → security',
    ],
    diagramKey: 'pipeline-overview',
    category: 'frontend',
    accentColor: '#fbbf24',
  },
  {
    id: 'portfolio',
    number: 12,
    title: 'Portfolio Integration',
    subtitle: 'This Page',
    description:
      'Wired all 11 stages into the Next.js 14 portfolio as an interactive deep-dive page. Features architecture diagram viewer with modal zoom, a 12-stage accordion explorer, live data charts via Recharts (with sample data fallback for the static site), and an API endpoint explorer.',
    techStack: ['Next.js 14', 'React', 'Recharts', 'Framer Motion', 'TypeScript'],
    highlights: [
      'Live API → sample data fallback',
      '4 interactive Recharts charts',
      'Architecture diagram modal viewer',
    ],
    category: 'frontend',
    accentColor: '#818cf8',
  },
];

export const categoryColors: Record<PipelineStage['category'], string> = {
  data: '#34d399',
  infrastructure: '#38bdf8',
  api: '#818cf8',
  frontend: '#fb7185',
};

export const categoryLabels: Record<PipelineStage['category'], string> = {
  data: 'Data Layer',
  infrastructure: 'Infrastructure',
  api: 'API Layer',
  frontend: 'Frontend',
};

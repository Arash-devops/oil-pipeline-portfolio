export type Project = {
  id: string;
  title: string;
  description: string;
  tags: string[];
  gradient: string;  // Tailwind gradient classes
  accentColor: string;
  githubUrl: string;
  liveUrl?: string;
  featured?: boolean;
};

export const projects: Project[] = [
  {
    id: 'oil-pipeline',
    title: 'Real-Time Oil Price Pipeline',
    description:
      'End-to-end streaming data pipeline that ingests live oil price feeds, processes them with Apache Spark Structured Streaming, orchestrates tasks via Airflow, and lands clean data into PostgreSQL for downstream analytics.',
    tags: ['Apache Spark', 'Kafka', 'Airflow', 'PostgreSQL', 'Python', 'Docker'],
    gradient: 'from-cyan-500/20 via-blue-500/10 to-indigo-500/20',
    accentColor: '#38bdf8',
    githubUrl: '#',
    featured: true,
  },
  {
    id: 'k8s-platform',
    title: 'K8s Microservices Platform',
    description:
      'Production-grade Kubernetes platform provisioned with Terraform, packaged with Helm charts, and wired into a full GitOps CI/CD pipeline. Includes observability stack with Prometheus and Grafana.',
    tags: ['Kubernetes', 'Terraform', 'Helm', 'CI/CD', 'Prometheus', 'GitOps'],
    gradient: 'from-indigo-500/20 via-purple-500/10 to-pink-500/20',
    accentColor: '#818cf8',
    githubUrl: '#',
    featured: true,
  },
  {
    id: 'lakehouse',
    title: 'Data Warehouse & Lakehouse',
    description:
      'Dimensional model built on PostgreSQL with Star Schema design, stored procedures for transformation logic, and a DuckDB analytics layer reading Parquet files directly from object storage.',
    tags: ['PostgreSQL', 'Star Schema', 'DuckDB', 'Parquet', 'Stored Procedures', 'SQL'],
    gradient: 'from-green-500/20 via-teal-500/10 to-cyan-500/20',
    accentColor: '#34d399',
    githubUrl: '#',
  },
  {
    id: 'ml-api',
    title: 'ML Model Serving API',
    description:
      'High-performance machine learning model serving layer built with FastAPI, containerised with Docker, and equipped with async endpoints, health checks, and request validation.',
    tags: ['FastAPI', 'Docker', 'Python', 'ML', 'REST', 'Pydantic'],
    gradient: 'from-amber-500/20 via-orange-500/10 to-rose-500/20',
    accentColor: '#fbbf24',
    githubUrl: '#',
  },
  {
    id: 'portfolio',
    title: 'This Portfolio Website',
    description:
      'Fully static personal portfolio built with Next.js 14, TypeScript, Tailwind CSS, and Framer Motion. Deployed to GitHub Pages via a GitHub Actions workflow.',
    tags: ['Next.js', 'React', 'TypeScript', 'Tailwind CSS', 'Framer Motion'],
    gradient: 'from-rose-500/20 via-pink-500/10 to-indigo-500/20',
    accentColor: '#fb7185',
    githubUrl: '#',
    liveUrl: '#',
  },
];

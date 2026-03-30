export type Technology = {
  name: string;
  level: number; // 0–100
};

export type Pillar = {
  id: string;
  title: string;
  description: string;
  color: string;          // Tailwind color key
  borderColor: string;    // actual CSS color for top border
  textColor: string;
  bgGlow: string;
  icon: string;           // emoji or svg path key
  proficiencies: { label: string; value: number }[];
  technologies: Technology[];
};

export const pillars: Pillar[] = [
  {
    id: 'devops',
    title: 'DevOps & Cloud',
    description:
      'Designing and operating scalable, resilient infrastructure. Automating delivery pipelines, managing container orchestration, and monitoring distributed systems across multi-cloud environments.',
    color: 'cyan',
    borderColor: '#38bdf8',
    textColor: 'text-cyan-400',
    bgGlow: 'rgba(56,189,248,0.08)',
    icon: '⚙️',
    proficiencies: [
      { label: 'Container Orchestration', value: 88 },
      { label: 'CI/CD Pipelines', value: 90 },
      { label: 'Cloud Platforms (AWS/GCP/Azure)', value: 80 },
      { label: 'Infrastructure as Code', value: 85 },
      { label: 'Observability & Monitoring', value: 78 },
    ],
    technologies: [
      { name: 'Docker', level: 92 },
      { name: 'Kubernetes', level: 88 },
      { name: 'Terraform', level: 85 },
      { name: 'Ansible', level: 80 },
      { name: 'Jenkins', level: 82 },
      { name: 'GitHub Actions', level: 90 },
      { name: 'GitLab CI', level: 85 },
      { name: 'AWS', level: 80 },
      { name: 'Azure', level: 75 },
      { name: 'GCP', level: 72 },
      { name: 'Prometheus', level: 78 },
      { name: 'Grafana', level: 80 },
      { name: 'Linux', level: 92 },
      { name: 'Nginx', level: 82 },
      { name: 'Helm', level: 80 },
    ],
  },
  {
    id: 'data',
    title: 'Data Engineering',
    description:
      'Building end-to-end data pipelines and lakehouses. Transforming raw data into reliable analytical foundations using modern data stack tools, stream processing, and dimensional modeling.',
    color: 'indigo',
    borderColor: '#818cf8',
    textColor: 'text-indigo-400',
    bgGlow: 'rgba(129,140,248,0.08)',
    icon: '📊',
    proficiencies: [
      { label: 'Stream & Batch Processing', value: 85 },
      { label: 'Data Modeling & Warehousing', value: 88 },
      { label: 'Pipeline Orchestration', value: 83 },
      { label: 'Cloud Data Platforms', value: 78 },
      { label: 'Analytics Engineering (dbt)', value: 80 },
    ],
    technologies: [
      { name: 'Apache Spark', level: 85 },
      { name: 'Kafka', level: 82 },
      { name: 'Airflow', level: 83 },
      { name: 'dbt', level: 80 },
      { name: 'Snowflake', level: 75 },
      { name: 'BigQuery', level: 78 },
      { name: 'PostgreSQL', level: 90 },
      { name: 'MongoDB', level: 78 },
      { name: 'Redis', level: 80 },
      { name: 'Pandas', level: 88 },
      { name: 'PySpark', level: 83 },
      { name: 'SQL', level: 92 },
      { name: 'Delta Lake', level: 78 },
      { name: 'Hadoop', level: 72 },
      { name: 'DuckDB', level: 80 },
      { name: 'Parquet', level: 82 },
      { name: 'Star Schema', level: 85 },
      { name: 'Stored Procedures', level: 80 },
    ],
  },
  {
    id: 'backend',
    title: 'Backend Development',
    description:
      'Crafting high-performance APIs and microservices. Applying security-first design patterns, event-driven architectures, and solid engineering principles across multiple languages and frameworks.',
    color: 'green',
    borderColor: '#34d399',
    textColor: 'text-green-400',
    bgGlow: 'rgba(52,211,153,0.08)',
    icon: '🖥️',
    proficiencies: [
      { label: 'Python / Go', value: 88 },
      { label: 'API Design (REST/gRPC/GraphQL)', value: 85 },
      { label: 'Microservices Architecture', value: 82 },
      { label: 'Message Queues', value: 80 },
      { label: 'Authentication & Security', value: 85 },
    ],
    technologies: [
      { name: 'Python', level: 92 },
      { name: 'Go', level: 80 },
      { name: 'Java', level: 75 },
      { name: 'Node.js', level: 78 },
      { name: 'FastAPI', level: 88 },
      { name: 'Django', level: 82 },
      { name: 'Spring Boot', level: 72 },
      { name: 'Express', level: 78 },
      { name: 'gRPC', level: 75 },
      { name: 'REST', level: 90 },
      { name: 'GraphQL', level: 78 },
      { name: 'RabbitMQ', level: 78 },
      { name: 'Celery', level: 80 },
      { name: 'OAuth 2.0', level: 82 },
    ],
  },
  {
    id: 'frontend',
    title: 'Frontend & Tooling',
    description:
      'Building responsive, accessible interfaces with modern React ecosystems. Comfortable with the full JS toolchain from bundling to deployment, and capable of producing polished data visualisations.',
    color: 'amber',
    borderColor: '#fbbf24',
    textColor: 'text-amber-400',
    bgGlow: 'rgba(251,191,36,0.08)',
    icon: '🎨',
    proficiencies: [
      { label: 'React / Next.js', value: 85 },
      { label: 'TypeScript', value: 88 },
      { label: 'CSS / Tailwind', value: 88 },
      { label: 'Build Tools & Bundlers', value: 78 },
      { label: 'Data Visualisation', value: 75 },
    ],
    technologies: [
      { name: 'React', level: 85 },
      { name: 'Next.js', level: 85 },
      { name: 'TypeScript', level: 88 },
      { name: 'Vue.js', level: 72 },
      { name: 'Tailwind CSS', level: 88 },
      { name: 'HTML5', level: 92 },
      { name: 'CSS3', level: 90 },
      { name: 'JavaScript', level: 85 },
      { name: 'Webpack', level: 75 },
      { name: 'Vite', level: 80 },
      { name: 'SASS', level: 80 },
      { name: 'D3.js', level: 70 },
    ],
  },
];

export const marqueeItems = [
  'Python', 'Go', 'TypeScript', 'Docker', 'Kubernetes', 'Terraform',
  'Apache Spark', 'Kafka', 'Airflow', 'dbt', 'PostgreSQL', 'React',
  'Next.js', 'FastAPI', 'AWS', 'GCP', 'Azure', 'Helm', 'Prometheus',
  'Grafana', 'GitHub Actions', 'GitLab CI', 'Redis', 'MongoDB',
  'DuckDB', 'Snowflake', 'BigQuery', 'PySpark', 'Ansible', 'Nginx',
];

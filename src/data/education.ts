export type Degree = {
  id: string;
  degree: string;
  field: string;
  institution: string;
  location: string;
  period: string;
  status: 'current' | 'completed';
  score?: string;
  description: string;
  tags: string[];
  color: string;
  dotColor: string;
};

export const degrees: Degree[] = [
  {
    id: 'cyber',
    degree: 'MSc',
    field: 'Cyber Security',
    institution: 'University in Germany',
    location: 'Germany',
    period: '2023 — Present',
    status: 'current',
    description:
      'Currently pursuing a Master\'s in Cyber Security, deepening expertise in network security, secure system design, cryptography, and threat analysis. Combining security principles with existing DevOps and data engineering knowledge to build defence-first architectures.',
    tags: ['Network Security', 'Cryptography', 'Threat Analysis', 'Secure Design', 'Penetration Testing'],
    color: 'text-rose-400',
    dotColor: '#fb7185',
  },
  {
    id: 'data-science',
    degree: 'MSc',
    field: 'Data Science',
    institution: 'Ulster University',
    location: 'Belfast, United Kingdom',
    period: '2021 — 2022',
    status: 'completed',
    score: 'Graduated with Distinction',
    description:
      'Completed a rigorous data science programme with Distinction, covering machine learning, statistical modelling, big data technologies, and data visualisation. Thesis work focused on applying ML pipelines to real-world analytical problems.',
    tags: ['Machine Learning', 'Statistical Modelling', 'Big Data', 'Python', 'Data Visualisation'],
    color: 'text-indigo-400',
    dotColor: '#818cf8',
  },
  {
    id: 'hardware',
    degree: 'MSc',
    field: 'Computer Hardware Engineering',
    institution: 'University',
    location: 'Iran',
    period: '2017 — 2019',
    status: 'completed',
    score: '16 / 20',
    description:
      'Built a deep foundation in computer architecture, embedded systems, digital circuit design, and low-level programming. This background provides a unique perspective on how software interacts with hardware, informing performance-conscious software design.',
    tags: ['Computer Architecture', 'Embedded Systems', 'Digital Design', 'FPGA', 'Low-Level Programming'],
    color: 'text-cyan-400',
    dotColor: '#38bdf8',
  },
];

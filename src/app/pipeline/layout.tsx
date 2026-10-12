import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "Oil Price Data Pipeline — Arash Razban",
  description:
    "Explore a commodity data pipeline with PostgreSQL, DuckDB, FastAPI, containerised deployment and observability.",
  alternates: { canonical: "https://arashrazban.com/pipeline/" },
};
export default function PipelineLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

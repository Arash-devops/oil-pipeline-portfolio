"""Pipeline orchestration: ties extractor -> validator -> loader together."""

from src.pipeline.ingestion_pipeline import IngestionPipeline

__all__ = ["IngestionPipeline"]

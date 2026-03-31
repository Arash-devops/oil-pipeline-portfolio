from setuptools import find_packages, setup

setup(
    name="oil-price-ingestor",
    version="0.1.0",
    description="Oil price data ingestion service for the oil_warehouse PostgreSQL data warehouse",
    author="Arash Razban",
    python_requires=">=3.12",
    packages=find_packages(where=".", include=["src*"]),
    install_requires=[
        "yfinance==0.2.40",
        "psycopg2-binary==2.9.9",
        "pydantic-settings==2.2.1",
        "pydantic==2.6.4",
        "pandas==2.2.1",
        "numpy==1.26.4",
        "python-dotenv==1.0.1",
    ],
    entry_points={
        "console_scripts": [
            "oil-ingestor=src.main:main",
        ],
    },
)

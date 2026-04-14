"""Generic ETL pipeline template: clean -> aggregate -> analyze -> anonymize."""

from .io_utils import load_csv, save_csv, log
from .cleaning import clean_source, run_cleaning
from .aggregation import run_aggregation
from .analysis import run_analysis
from .anonymization import anonymize_tables
from .excel_writer import write_report

__all__ = [
    "load_csv",
    "save_csv",
    "log",
    "clean_source",
    "run_cleaning",
    "run_aggregation",
    "run_analysis",
    "anonymize_tables",
    "write_report",
]

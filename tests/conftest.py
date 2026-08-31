import sys

from datagouv_toolkit import (
    catalog_stats,
    cli,
    datagouv,
    dataset_workflow,
    download_resources,
    inspect_csv,
    normalize,
)

sys.modules["catalog_stats"] = catalog_stats
sys.modules["cli"] = cli
sys.modules["datagouv"] = datagouv
sys.modules["dataset_workflow"] = dataset_workflow
sys.modules["download_resources"] = download_resources
sys.modules["inspect_csv"] = inspect_csv
sys.modules["normalize"] = normalize

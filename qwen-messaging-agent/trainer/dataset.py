"""
Dataset preparation utilities
"""
from datasets import load_dataset, concatenate_datasets


def load_conversational_datasets():
    """Load and combine multiple conversational datasets.

    Returns a single concatenated dataset or None if all loads fail.
    """
    datasets_to_load = [
        ("OpenAssistant/oasst2", "train"),
        ("allenai/ultrafeedback_binarized_cleaned", "train[:5000]"),
        ("HuggingFaceH4/no_robots", "train[:5000]"),
    ]

    loaded_datasets = []
    for dataset_name, split in datasets_to_load:
        try:
            ds = load_dataset(dataset_name, split=split)
            loaded_datasets.append(ds)
        except Exception as e:  # noqa: BLE001 - best effort loading optional datasets
            print(f"Failed to load {dataset_name}: {e}")

    if loaded_datasets:
        return concatenate_datasets(loaded_datasets)
    return None



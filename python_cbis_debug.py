import pandas as pd
from pathlib import Path
import glob


def debug_csv_structure(base_path):
    """Debug the CSV structure to understand the mapping"""
    base_path = Path(base_path)
    csv_path = base_path / "csv"

    print("=== CSV File Analysis ===")

    # Load and examine each CSV file
    csv_files = {
        'calc_train': 'calc_case_description_train_set.csv',
        'calc_test': 'calc_case_description_test_set.csv',
        'mass_train': 'mass_case_description_train_set.csv',
        'mass_test': 'mass_case_description_test_set.csv',
        'meta': 'meta.csv',
        'dicom_info': 'dicom_info.csv'
    }

    for key, filename in csv_files.items():
        file_path = csv_path / filename
        if file_path.exists():
            print(f"\n--- {filename} ---")
            df = pd.read_csv(file_path)
            print(f"Shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")

            # Show first few rows
            print("\nFirst 3 rows:")
            print(df.head(3))

            # Look for image-related columns
            img_cols = [col for col in df.columns if
                        any(word in col.lower() for word in ['image', 'file', 'path', 'series', 'study'])]
            if img_cols:
                print(f"\nImage-related columns: {img_cols}")
                for col in img_cols:
                    print(f"Sample {col} values:")
                    print(df[col].head(3).tolist())

    print("\n=== Image File Analysis ===")

    # Find all JPEG files
    jpeg_path = base_path / "jpeg"
    jpeg_files = []
    for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
        jpeg_files.extend(glob.glob(str(jpeg_path / "**" / ext), recursive=True))

    print(f"Found {len(jpeg_files)} JPEG files")
    print("Sample JPEG file paths:")
    for i, file_path in enumerate(jpeg_files[:10]):
        print(f"  {Path(file_path).name} -> {file_path}")

    # Analyze directory structure
    print("\n=== Directory Structure Analysis ===")
    for jpeg_file in jpeg_files[:20]:
        path = Path(jpeg_file)
        print(f"File: {path.name}")
        print(f"  Full path: {path}")
        print(f"  Parent dirs: {path.parent.parts}")
        print(f"  Relative to jpeg: {path.relative_to(jpeg_path)}")
        print()


def find_mapping_strategy(base_path):
    """Try to find the correct mapping strategy"""
    base_path = Path(base_path)
    csv_path = base_path / "csv"

    print("\n=== Finding Mapping Strategy ===")

    # Load case description files
    case_files = [
        'calc_case_description_train_set.csv',
        'calc_case_description_test_set.csv',
        'mass_case_description_train_set.csv',
        'mass_case_description_test_set.csv'
    ]

    for filename in case_files:
        file_path = csv_path / filename
        if file_path.exists():
            print(f"\n--- Analyzing {filename} ---")
            df = pd.read_csv(file_path)

            # Common columns in CBIS-DDSM case description files
            key_cols = ['patient_id', 'study_instance_uid', 'series_instance_uid', 'series_description']

            for col in key_cols:
                if col in df.columns:
                    print(f"{col}: {df[col].head(3).tolist()}")

            # Check if there's an image file path column
            path_cols = [col for col in df.columns if 'path' in col.lower() or 'file' in col.lower()]
            if path_cols:
                print(f"Path columns: {path_cols}")
                for col in path_cols:
                    print(f"{col}: {df[col].head(3).tolist()}")


def create_improved_organizer(base_path):
    """Create an improved organizer based on findings"""
    print("\n=== Creating Improved Mapping ===")

    base_path = Path(base_path)
    csv_path = base_path / "csv"

    # Load dicom_info.csv to understand SeriesInstanceUID mapping
    dicom_info_path = csv_path / "dicom_info.csv"
    meta_path = csv_path / "meta.csv"

    if dicom_info_path.exists() and meta_path.exists():
        dicom_df = pd.read_csv(dicom_info_path)
        meta_df = pd.read_csv(meta_path)

        print("DICOM Info columns:", dicom_df.columns.tolist())
        print("Meta columns:", meta_df.columns.tolist())

        # Check if we can map SeriesInstanceUID to actual file paths
        if 'SeriesInstanceUID' in dicom_df.columns:
            print("\nSample SeriesInstanceUID from dicom_info:")
            print(dicom_df['SeriesInstanceUID'].head(3).tolist())

        # Look for file paths in dicom_info
        path_cols = [col for col in dicom_df.columns if any(word in col.lower() for word in ['path', 'file', 'name'])]
        if path_cols:
            print(f"\nPath columns in dicom_info: {path_cols}")
            for col in path_cols:
                print(f"{col}: {dicom_df[col].head(3).tolist()}")


if __name__ == "__main__":
    # Update this path to match your dataset location
    dataset_path = "/home/mdbasit_tezu_ernet_in/.cache/kagglehub/datasets/awsaf49/cbis-ddsm-breast-cancer-image-dataset/versions/1"

    debug_csv_structure(dataset_path)
    find_mapping_strategy(dataset_path)
    create_improved_organizer(dataset_path)
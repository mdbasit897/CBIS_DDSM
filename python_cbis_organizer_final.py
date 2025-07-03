import os
import shutil
import pandas as pd
from pathlib import Path
import glob


class CBISDDSMOrganizer:
    def __init__(self, base_path):
        """
        Initialize the organizer with the base path of your dataset

        Args:
            base_path (str): Path to your CBIS-DDSM dataset folder
        """
        self.base_path = Path(base_path)
        self.jpeg_path = self.base_path / "jpeg"
        self.csv_path = self.base_path / "csv"

        # Create output directories
        self.calc_dir = self.base_path / "organized" / "calcifications"
        self.mass_dir = self.base_path / "organized" / "masses"

        # Create directories if they don't exist
        self.calc_dir.mkdir(parents=True, exist_ok=True)
        self.mass_dir.mkdir(parents=True, exist_ok=True)

    def load_csv_files(self):
        """Load all CSV files and combine them"""
        csv_files = {
            'calc_train': 'calc_case_description_train_set.csv',
            'calc_test': 'calc_case_description_test_set.csv',
            'mass_train': 'mass_case_description_train_set.csv',
            'mass_test': 'mass_case_description_test_set.csv',
            'meta': 'meta.csv',
            'dicom_info': 'dicom_info.csv'
        }

        self.dataframes = {}

        for key, filename in csv_files.items():
            file_path = self.csv_path / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    self.dataframes[key] = df
                    print(f"Loaded {filename}: {len(df)} rows")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
            else:
                print(f"Warning: {filename} not found")

    def get_image_mappings(self):
        """
        Create mappings between image filenames and their categories
        This function may need adjustment based on your specific CSV structure
        """
        calc_images = set()
        mass_images = set()

        # Method 1: Using case description files
        for key, df in self.dataframes.items():
            if 'calc' in key and df is not None:
                # Look for columns that might contain image references
                possible_cols = ['image file path', 'file_path', 'image_path', 'SeriesInstanceUID']
                for col in possible_cols:
                    if col in df.columns:
                        calc_images.update(df[col].dropna().astype(str))
                        break

            elif 'mass' in key and df is not None:
                # Look for columns that might contain image references
                possible_cols = ['image file path', 'file_path', 'image_path', 'SeriesInstanceUID']
                for col in possible_cols:
                    if col in df.columns:
                        mass_images.update(df[col].dropna().astype(str))
                        break

        # Method 2: Using meta.csv or dicom_info.csv if available
        if 'meta' in self.dataframes and self.dataframes['meta'] is not None:
            meta_df = self.dataframes['meta']
            print("Meta.csv columns:", meta_df.columns.tolist())

            # Look for category indicators in meta.csv
            category_cols = ['abnormality', 'pathology', 'category', 'type']
            for col in category_cols:
                if col in meta_df.columns:
                    calc_meta = meta_df[meta_df[col].str.contains('calc', case=False, na=False)]
                    mass_meta = meta_df[meta_df[col].str.contains('mass', case=False, na=False)]

                    # Extract image references
                    img_cols = ['image file path', 'file_path', 'SeriesInstanceUID']
                    for img_col in img_cols:
                        if img_col in meta_df.columns:
                            calc_images.update(calc_meta[img_col].dropna().astype(str))
                            mass_images.update(mass_meta[img_col].dropna().astype(str))
                            break
                    break

        return calc_images, mass_images

    def find_all_jpeg_files(self):
        """Find all JPEG files in the dataset"""
        jpeg_files = []

        # Search for all .jpg files recursively
        for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
            jpeg_files.extend(glob.glob(str(self.jpeg_path / "**" / ext), recursive=True))

        return [Path(f) for f in jpeg_files]

    def organize_images_by_filename_pattern(self):
        """
        Organize images based on filename patterns if CSV mapping doesn't work
        This is a fallback method
        """
        all_images = self.find_all_jpeg_files()
        print(f"Found {len(all_images)} JPEG files")

        calc_moved = 0
        mass_moved = 0
        unknown_moved = 0

        for img_path in all_images:
            # Try to determine type from parent directory names or file structure
            path_str = str(img_path).lower()

            # Check if path contains calc or mass indicators
            if 'calc' in path_str:
                destination = self.calc_dir / img_path.name
                shutil.copy2(img_path, destination)
                calc_moved += 1
                print(f"Moved to calcifications: {img_path.name}")
            elif 'mass' in path_str:
                destination = self.mass_dir / img_path.name
                shutil.copy2(img_path, destination)
                mass_moved += 1
                print(f"Moved to masses: {img_path.name}")
            else:
                # For unknown categorization, you might want to examine the CSV files
                unknown_dir = self.base_path / "organized" / "unknown"
                unknown_dir.mkdir(parents=True, exist_ok=True)
                destination = unknown_dir / img_path.name
                shutil.copy2(img_path, destination)
                unknown_moved += 1
                print(f"Moved to unknown: {img_path.name}")

        print(f"\nSummary:")
        print(f"Calcifications: {calc_moved}")
        print(f"Masses: {mass_moved}")
        print(f"Unknown: {unknown_moved}")

    def organize_images_by_csv_mapping(self):
        """Organize images using CSV file mappings"""
        calc_images, mass_images = self.get_image_mappings()
        all_images = self.find_all_jpeg_files()

        print(f"Found {len(calc_images)} calcification references")
        print(f"Found {len(mass_images)} mass references")
        print(f"Found {len(all_images)} total JPEG files")

        calc_moved = 0
        mass_moved = 0
        unmatched = 0

        for img_path in all_images:
            img_name = img_path.name
            img_stem = img_path.stem

            # Try to match with calc images
            matched = False
            for calc_ref in calc_images:
                if img_name in calc_ref or img_stem in calc_ref or calc_ref in str(img_path):
                    destination = self.calc_dir / img_name
                    shutil.copy2(img_path, destination)
                    calc_moved += 1
                    matched = True
                    print(f"Moved to calcifications: {img_name}")
                    break

            if not matched:
                # Try to match with mass images
                for mass_ref in mass_images:
                    if img_name in mass_ref or img_stem in mass_ref or mass_ref in str(img_path):
                        destination = self.mass_dir / img_name
                        shutil.copy2(img_path, destination)
                        mass_moved += 1
                        matched = True
                        print(f"Moved to masses: {img_name}")
                        break

            if not matched:
                unmatched += 1
                print(f"Unmatched: {img_name}")

        print(f"\nSummary:")
        print(f"Calcifications: {calc_moved}")
        print(f"Masses: {mass_moved}")
        print(f"Unmatched: {unmatched}")

    def run(self, method='csv'):
        """
        Run the organization process

        Args:
            method (str): 'csv' to use CSV mappings, 'pattern' to use filename patterns
        """
        print("Starting CBIS-DDSM image organization...")
        print(f"Base path: {self.base_path}")

        self.load_csv_files()

        if method == 'csv':
            print("Using CSV mapping method...")
            self.organize_images_by_csv_mapping()
        else:
            print("Using filename pattern method...")
            self.organize_images_by_filename_pattern()

        print("Organization complete!")


# Usage
if __name__ == "__main__":
    # Update this path to match your dataset location
    dataset_path = "/home/mdbasit_tezu_ernet_in/.cache/kagglehub/datasets/awsaf49/cbis-ddsm-breast-cancer-image-dataset/versions/1"

    organizer = CBISDDSMOrganizer(dataset_path)

    # Try CSV mapping first, fall back to pattern matching if needed
    try:
        organizer.run(method='csv')
    except Exception as e:
        print(f"CSV method failed: {e}")
        print("Falling back to pattern matching...")
        organizer.run(method='pattern')
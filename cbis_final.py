import os
import shutil
import pandas as pd
from pathlib import Path
import glob


class CBISDDSMCompleteOrganizer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.jpeg_path = self.base_path / "jpeg"
        self.csv_path = self.base_path / "csv"

        # Create output directories
        self.calc_dir = self.base_path / "organized" / "calcifications"
        self.mass_dir = self.base_path / "organized" / "masses"
        self.unknown_dir = self.base_path / "organized" / "unknown"

        # Create directories if they don't exist
        self.calc_dir.mkdir(parents=True, exist_ok=True)
        self.mass_dir.mkdir(parents=True, exist_ok=True)
        self.unknown_dir.mkdir(parents=True, exist_ok=True)

        print(f"🚀 CBIS-DDSM Complete Organizer")
        print(f"📁 Dataset: {self.base_path}")
        print(f"📁 JPEG folder: {self.jpeg_path}")
        print(f"📁 Output: {self.base_path / 'organized'}")

    def create_comprehensive_mapping(self):
        """Create comprehensive mapping using multiple sources"""

        print(f"\n=== CREATING COMPREHENSIVE MAPPING ===")

        # Method 1: Use dicom_info.csv
        mapping_from_dicom = self.get_mapping_from_dicom_info()

        # Method 2: Use SeriesInstanceUID from case description files
        mapping_from_case_files = self.get_mapping_from_case_files()

        # Method 3: Use directory structure patterns
        mapping_from_directory = self.get_mapping_from_directory()

        # Combine all mappings
        final_mapping = {}

        # Priority: dicom_info > case_files > directory
        final_mapping.update(mapping_from_directory)
        final_mapping.update(mapping_from_case_files)
        final_mapping.update(mapping_from_dicom)

        print(f"\nMapping sources:")
        print(f"  - From dicom_info.csv: {len(mapping_from_dicom)}")
        print(f"  - From case files: {len(mapping_from_case_files)}")
        print(f"  - From directory: {len(mapping_from_directory)}")
        print(f"  - Final combined: {len(final_mapping)}")

        return final_mapping

    def get_mapping_from_dicom_info(self):
        """Get mapping from dicom_info.csv"""
        dicom_info_path = self.csv_path / "dicom_info.csv"

        if not dicom_info_path.exists():
            return {}

        df = pd.read_csv(dicom_info_path)
        mapping = {}

        for _, row in df.iterrows():
            image_path = row['image_path']
            patient_name = row['PatientName']

            if pd.isna(image_path):
                continue

            filename = Path(image_path).name

            # Determine category from PatientName
            if pd.notna(patient_name):
                patient_name_str = str(patient_name).lower()
                if 'mass' in patient_name_str:
                    category = 'mass'
                elif 'calc' in patient_name_str:
                    category = 'calc'
                else:
                    category = 'unknown'
            else:
                category = 'unknown'

            mapping[filename] = {
                'category': category,
                'source': 'dicom_info',
                'patient_name': patient_name
            }

        return mapping

    def get_mapping_from_case_files(self):
        """Get mapping from case description files using SeriesInstanceUID"""
        mapping = {}

        # Load case description files
        case_files = {
            'calc': ['calc_case_description_train_set.csv', 'calc_case_description_test_set.csv'],
            'mass': ['mass_case_description_train_set.csv', 'mass_case_description_test_set.csv']
        }

        # Load dicom_info for SeriesInstanceUID to filename mapping
        dicom_info_path = self.csv_path / "dicom_info.csv"
        if not dicom_info_path.exists():
            return mapping

        dicom_df = pd.read_csv(dicom_info_path)

        # Create SeriesInstanceUID to filename mapping
        series_to_filename = {}
        for _, row in dicom_df.iterrows():
            if pd.notna(row['image_path']) and pd.notna(row['SeriesInstanceUID']):
                filename = Path(row['image_path']).name
                series_uid = str(row['SeriesInstanceUID'])
                series_to_filename[series_uid] = filename

        # Process each case file
        for category, filenames in case_files.items():
            for filename in filenames:
                file_path = self.csv_path / filename
                if not file_path.exists():
                    continue

                df = pd.read_csv(file_path)

                # Look for SeriesInstanceUID in image file paths
                for _, row in df.iterrows():
                    image_file_path = row.get('image file path', '')
                    if pd.isna(image_file_path):
                        continue

                    # Extract SeriesInstanceUID from path
                    # Format: "Category_Patient_View/SeriesInstanceUID/SeriesInstanceUID/000000.dcm"
                    path_parts = str(image_file_path).split('/')
                    if len(path_parts) >= 2:
                        series_uid = path_parts[1]  # Second part is SeriesInstanceUID

                        if series_uid in series_to_filename:
                            filename = series_to_filename[series_uid]
                            mapping[filename] = {
                                'category': category,
                                'source': 'case_files',
                                'series_uid': series_uid
                            }

        return mapping

    def get_mapping_from_directory(self):
        """Get mapping from directory structure analysis"""
        mapping = {}

        # Find all JPEG files
        all_images = []
        for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
            all_images.extend(glob.glob(str(self.jpeg_path / "**" / ext), recursive=True))

        # Analyze directory structure
        for img_path in all_images:
            img_path = Path(img_path)
            filename = img_path.name

            # Skip if already mapped
            if filename in mapping:
                continue

            # Try to determine category from path
            try:
                rel_path = img_path.relative_to(self.jpeg_path)
                path_str = str(rel_path).lower()

                # Check if SeriesInstanceUID appears in any case file
                series_uid = rel_path.parts[0]  # First part is SeriesInstanceUID

                # Default to unknown for directory-based mapping
                category = 'unknown'

                mapping[filename] = {
                    'category': category,
                    'source': 'directory',
                    'series_uid': series_uid
                }

            except ValueError:
                # If relative path calculation fails
                mapping[filename] = {
                    'category': 'unknown',
                    'source': 'directory',
                    'series_uid': 'unknown'
                }

        return mapping

    def organize_images(self):
        """Organize all images using comprehensive mapping"""

        print(f"\n=== STARTING ORGANIZATION ===")

        # Create comprehensive mapping
        final_mapping = self.create_comprehensive_mapping()

        # Find all JPEG files
        all_images = []
        for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
            all_images.extend(glob.glob(str(self.jpeg_path / "**" / ext), recursive=True))

        print(f"Found {len(all_images)} JPEG files")
        print(f"Have mapping for {len(final_mapping)} files")

        # Organize images
        calc_moved = 0
        mass_moved = 0
        unknown_moved = 0

        for img_path in all_images:
            img_path = Path(img_path)
            filename = img_path.name

            # Get category from mapping
            if filename in final_mapping:
                category = final_mapping[filename]['category']
                source = final_mapping[filename]['source']
            else:
                category = 'unknown'
                source = 'not_mapped'

            # Move to appropriate directory
            if category == 'calc':
                destination = self.calc_dir / filename
                shutil.copy2(img_path, destination)
                calc_moved += 1
                if calc_moved <= 10:
                    print(f"Calc: {filename} ({source})")
            elif category == 'mass':
                destination = self.mass_dir / filename
                shutil.copy2(img_path, destination)
                mass_moved += 1
                if mass_moved <= 10:
                    print(f"Mass: {filename} ({source})")
            else:
                destination = self.unknown_dir / filename
                shutil.copy2(img_path, destination)
                unknown_moved += 1
                if unknown_moved <= 10:
                    print(f"Unknown: {filename} ({source})")

        print(f"\n=== ORGANIZATION COMPLETE ===")
        print(f"📊 Results:")
        print(f"  - Calcifications: {calc_moved}")
        print(f"  - Masses: {mass_moved}")
        print(f"  - Unknown: {unknown_moved}")
        print(f"  - Total: {calc_moved + mass_moved + unknown_moved}")

        return {
            'calc_moved': calc_moved,
            'mass_moved': mass_moved,
            'unknown_moved': unknown_moved
        }

    def verify_organization(self):
        """Verify the organization results"""
        print(f"\n=== VERIFICATION ===")

        calc_files = list(self.calc_dir.glob("*.jpg"))
        mass_files = list(self.mass_dir.glob("*.jpg"))
        unknown_files = list(self.unknown_dir.glob("*.jpg"))

        print(f"📁 Actual files moved:")
        print(f"  - Calcifications: {len(calc_files)}")
        print(f"  - Masses: {len(mass_files)}")
        print(f"  - Unknown: {len(unknown_files)}")
        print(f"  - Total: {len(calc_files) + len(mass_files) + len(unknown_files)}")

        # Show samples
        if calc_files:
            print(f"\n📋 Sample calcification files:")
            for f in calc_files[:5]:
                print(f"  - {f.name}")

        if mass_files:
            print(f"\n📋 Sample mass files:")
            for f in mass_files[:5]:
                print(f"  - {f.name}")

        if unknown_files:
            print(f"\n📋 Sample unknown files:")
            for f in unknown_files[:5]:
                print(f"  - {f.name}")


def main():
    dataset_path = "/home/mdbasit_tezu_ernet_in/.cache/kagglehub/datasets/awsaf49/cbis-ddsm-breast-cancer-image-dataset/versions/1"

    try:
        organizer = CBISDDSMCompleteOrganizer(dataset_path)

        # Organize images
        results = organizer.organize_images()

        # Verify results
        organizer.verify_organization()

        print(f"\n✅ Organization complete!")
        print(f"📁 Your organized images are in: {Path(dataset_path) / 'organized'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
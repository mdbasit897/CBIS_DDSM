import os
import shutil
import pandas as pd
from pathlib import Path
import glob


class CBISDDSMFixedOrganizer:
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

        print(f"🚀 CBIS-DDSM Fixed Organizer")
        print(f"📁 Dataset: {self.base_path}")

    def create_complete_mapping(self):
        """Create complete mapping for ALL 10,237 files"""

        print(f"\n=== CREATING COMPLETE MAPPING ===")

        # Step 1: Load dicom_info.csv and create SeriesInstanceUID to filename mapping
        dicom_info_path = self.csv_path / "dicom_info.csv"
        dicom_df = pd.read_csv(dicom_info_path)

        # Create SeriesInstanceUID -> filename mapping
        series_to_filename = {}
        filename_to_series = {}

        for _, row in dicom_df.iterrows():
            if pd.notna(row['image_path']) and pd.notna(row['SeriesInstanceUID']):
                filename = Path(row['image_path']).name
                series_uid = str(row['SeriesInstanceUID'])
                series_to_filename[series_uid] = filename
                filename_to_series[filename] = series_uid

        print(f"Created SeriesInstanceUID mappings: {len(series_to_filename)}")

        # Step 2: Create category mappings from case description files
        calc_series = set()
        mass_series = set()

        # Process calc files
        calc_files = ['calc_case_description_train_set.csv', 'calc_case_description_test_set.csv']
        for filename in calc_files:
            file_path = self.csv_path / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                for _, row in df.iterrows():
                    image_path = row.get('image file path', '')
                    if pd.notna(image_path):
                        # Extract SeriesInstanceUID from path
                        # Format: "Calc-Training_Patient/SeriesInstanceUID/SeriesInstanceUID/000000.dcm"
                        path_parts = str(image_path).split('/')
                        if len(path_parts) >= 2:
                            series_uid = path_parts[1]
                            calc_series.add(series_uid)

        # Process mass files
        mass_files = ['mass_case_description_train_set.csv', 'mass_case_description_test_set.csv']
        for filename in mass_files:
            file_path = self.csv_path / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                for _, row in df.iterrows():
                    image_path = row.get('image file path', '')
                    if pd.notna(image_path):
                        # Extract SeriesInstanceUID from path
                        path_parts = str(image_path).split('/')
                        if len(path_parts) >= 2:
                            series_uid = path_parts[1]
                            mass_series.add(series_uid)

        print(f"Found calc SeriesInstanceUIDs: {len(calc_series)}")
        print(f"Found mass SeriesInstanceUIDs: {len(mass_series)}")

        # Step 3: Create complete filename mapping
        final_mapping = {}

        # Find all JPEG files
        all_images = []
        for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
            all_images.extend(glob.glob(str(self.jpeg_path / "**" / ext), recursive=True))

        print(f"Found {len(all_images)} JPEG files")

        # Create mapping for each file
        for img_path in all_images:
            img_path = Path(img_path)
            filename = img_path.name

            # Get SeriesInstanceUID from directory structure
            try:
                rel_path = img_path.relative_to(self.jpeg_path)
                series_uid = rel_path.parts[0]  # First part is SeriesInstanceUID
            except:
                series_uid = 'unknown'

            # Determine category
            category = 'unknown'
            source = 'default'

            # Method 1: Check if SeriesInstanceUID is in case files
            if series_uid in calc_series:
                category = 'calc'
                source = 'case_files'
            elif series_uid in mass_series:
                category = 'mass'
                source = 'case_files'
            else:
                # Method 2: Check dicom_info PatientName
                if filename in filename_to_series:
                    # Find the row in dicom_info
                    matching_rows = dicom_df[dicom_df['SeriesInstanceUID'] == filename_to_series[filename]]
                    if not matching_rows.empty:
                        patient_name = matching_rows.iloc[0]['PatientName']
                        if pd.notna(patient_name):
                            patient_name_str = str(patient_name).lower()
                            if 'mass' in patient_name_str:
                                category = 'mass'
                                source = 'dicom_info'
                            elif 'calc' in patient_name_str:
                                category = 'calc'
                                source = 'dicom_info'

            final_mapping[filename] = {
                'category': category,
                'source': source,
                'series_uid': series_uid,
                'full_path': img_path
            }

        # Count categories
        calc_count = sum(1 for info in final_mapping.values() if info['category'] == 'calc')
        mass_count = sum(1 for info in final_mapping.values() if info['category'] == 'mass')
        unknown_count = sum(1 for info in final_mapping.values() if info['category'] == 'unknown')

        print(f"\nComplete mapping created:")
        print(f"  - Total files: {len(final_mapping)}")
        print(f"  - Calc: {calc_count}")
        print(f"  - Mass: {mass_count}")
        print(f"  - Unknown: {unknown_count}")

        return final_mapping

    def organize_images(self):
        """Organize all images using the complete mapping"""

        print(f"\n=== ORGANIZING ALL IMAGES ===")

        # Create complete mapping
        final_mapping = self.create_complete_mapping()

        # Organize images
        calc_moved = 0
        mass_moved = 0
        unknown_moved = 0
        errors = 0

        for filename, info in final_mapping.items():
            try:
                source_path = info['full_path']
                category = info['category']

                # Move to appropriate directory
                if category == 'calc':
                    destination = self.calc_dir / filename
                    shutil.copy2(source_path, destination)
                    calc_moved += 1
                    if calc_moved <= 10:
                        print(f"✅ Calc: {filename} ({info['source']})")
                elif category == 'mass':
                    destination = self.mass_dir / filename
                    shutil.copy2(source_path, destination)
                    mass_moved += 1
                    if mass_moved <= 10:
                        print(f"✅ Mass: {filename} ({info['source']})")
                else:
                    destination = self.unknown_dir / filename
                    shutil.copy2(source_path, destination)
                    unknown_moved += 1
                    if unknown_moved <= 10:
                        print(f"❓ Unknown: {filename} ({info['source']})")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"❌ Error moving {filename}: {e}")

        print(f"\n=== ORGANIZATION COMPLETE ===")
        print(f"📊 Files processed:")
        print(f"  - Calcifications: {calc_moved}")
        print(f"  - Masses: {mass_moved}")
        print(f"  - Unknown: {unknown_moved}")
        print(f"  - Errors: {errors}")
        print(f"  - Total: {calc_moved + mass_moved + unknown_moved}")

        return {
            'calc_moved': calc_moved,
            'mass_moved': mass_moved,
            'unknown_moved': unknown_moved,
            'errors': errors
        }

    def verify_organization(self):
        """Verify the final organization"""
        print(f"\n=== FINAL VERIFICATION ===")

        calc_files = list(self.calc_dir.glob("*.jpg"))
        mass_files = list(self.mass_dir.glob("*.jpg"))
        unknown_files = list(self.unknown_dir.glob("*.jpg"))

        total_organized = len(calc_files) + len(mass_files) + len(unknown_files)

        print(f"📁 Final counts:")
        print(f"  - Calcifications: {len(calc_files)}")
        print(f"  - Masses: {len(mass_files)}")
        print(f"  - Unknown: {len(unknown_files)}")
        print(f"  - Total organized: {total_organized}")

        # Check if all files were organized
        if total_organized == 10237:
            print(f"✅ SUCCESS: All 10,237 images organized!")
        else:
            print(f"⚠️  WARNING: Expected 10,237 images, but organized {total_organized}")

        return total_organized


def main():
    dataset_path = "/home/mdbasit_tezu_ernet_in/.cache/kagglehub/datasets/awsaf49/cbis-ddsm-breast-cancer-image-dataset/versions/1"

    try:
        organizer = CBISDDSMFixedOrganizer(dataset_path)

        # Organize images
        results = organizer.organize_images()

        # Verify results
        total_organized = organizer.verify_organization()

        if total_organized == 10237:
            print(f"\n🎉 PERFECT! All images successfully organized!")
        else:
            print(f"\n⚠️  {total_organized} images organized out of 10,237")

        print(f"📁 Your organized images are in: {Path(dataset_path) / 'organized'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
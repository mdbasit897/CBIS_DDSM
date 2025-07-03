import os
import shutil
import pandas as pd
from pathlib import Path
import glob


class CBISDDSMCorrectOrganizer:
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

        print(f"🚀 CBIS-DDSM CORRECT Organizer")
        print(f"📁 Dataset: {self.base_path}")

    def get_calc_series_uids(self):
        """Get all SeriesInstanceUIDs from calc case files"""
        calc_series = set()

        calc_files = ['calc_case_description_train_set.csv', 'calc_case_description_test_set.csv']

        for filename in calc_files:
            file_path = self.csv_path / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                print(f"Loading {filename}: {len(df)} rows")

                # Extract SeriesInstanceUID from image file path
                for _, row in df.iterrows():
                    image_path = row.get('image file path', '')
                    if pd.notna(image_path) and image_path.strip():
                        # Path format: "Calc-Training_Patient/SeriesInstanceUID/SeriesInstanceUID/000000.dcm"
                        path_parts = str(image_path).split('/')
                        if len(path_parts) >= 2:
                            series_uid = path_parts[1]  # Second part is the SeriesInstanceUID
                            calc_series.add(series_uid)

        print(f"Found {len(calc_series)} unique calc SeriesInstanceUIDs")
        return calc_series

    def get_mass_series_uids(self):
        """Get all SeriesInstanceUIDs from mass case files"""
        mass_series = set()

        mass_files = ['mass_case_description_train_set.csv', 'mass_case_description_test_set.csv']

        for filename in mass_files:
            file_path = self.csv_path / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                print(f"Loading {filename}: {len(df)} rows")

                # Extract SeriesInstanceUID from image file path
                for _, row in df.iterrows():
                    image_path = row.get('image file path', '')
                    if pd.notna(image_path) and image_path.strip():
                        # Path format: "Mass-Training_Patient/SeriesInstanceUID/SeriesInstanceUID/000000.dcm"
                        path_parts = str(image_path).split('/')
                        if len(path_parts) >= 2:
                            series_uid = path_parts[1]  # Second part is the SeriesInstanceUID
                            mass_series.add(series_uid)

        print(f"Found {len(mass_series)} unique mass SeriesInstanceUIDs")
        return mass_series

    def organize_all_images(self):
        """Organize ALL images based on their SeriesInstanceUID"""

        print(f"\n=== ORGANIZING ALL 10,237 IMAGES ===")

        # Get SeriesInstanceUID sets
        calc_series = self.get_calc_series_uids()
        mass_series = self.get_mass_series_uids()

        # Find all JPEG files
        all_images = []
        for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
            all_images.extend(glob.glob(str(self.jpeg_path / "**" / ext), recursive=True))

        print(f"Found {len(all_images)} JPEG files")

        # Organize every single image
        calc_moved = 0
        mass_moved = 0
        unknown_moved = 0
        errors = 0

        for img_path in all_images:
            try:
                img_path = Path(img_path)
                filename = img_path.name

                # Get SeriesInstanceUID from directory structure
                # Structure: /jpeg/SeriesInstanceUID/filename.jpg
                try:
                    rel_path = img_path.relative_to(self.jpeg_path)
                    series_uid = rel_path.parts[0]  # First part is SeriesInstanceUID
                except:
                    series_uid = 'unknown'

                # Determine category based on SeriesInstanceUID
                if series_uid in calc_series:
                    destination = self.calc_dir / filename
                    shutil.copy2(img_path, destination)
                    calc_moved += 1
                    category = 'calc'
                elif series_uid in mass_series:
                    destination = self.mass_dir / filename
                    shutil.copy2(img_path, destination)
                    mass_moved += 1
                    category = 'mass'
                else:
                    destination = self.unknown_dir / filename
                    shutil.copy2(img_path, destination)
                    unknown_moved += 1
                    category = 'unknown'

                # Show progress for first 20 files
                total_moved = calc_moved + mass_moved + unknown_moved
                if total_moved <= 20:
                    print(f"✅ {category.upper()}: {filename} (SeriesUID: {series_uid[:20]}...)")
                elif total_moved % 1000 == 0:
                    print(f"📊 Progress: {total_moved:,} files processed...")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"❌ Error processing {img_path}: {e}")

        print(f"\n=== ORGANIZATION COMPLETE ===")
        print(f"📊 Final Results:")
        print(f"  - Calcifications: {calc_moved:,}")
        print(f"  - Masses: {mass_moved:,}")
        print(f"  - Unknown: {unknown_moved:,}")
        print(f"  - Errors: {errors}")
        print(f"  - Total processed: {calc_moved + mass_moved + unknown_moved:,}")

        return calc_moved, mass_moved, unknown_moved, errors

    def verify_final_organization(self):
        """Final verification of all organized files"""
        print(f"\n=== FINAL VERIFICATION ===")

        calc_files = list(self.calc_dir.glob("*.jpg"))
        mass_files = list(self.mass_dir.glob("*.jpg"))
        unknown_files = list(self.unknown_dir.glob("*.jpg"))

        total_organized = len(calc_files) + len(mass_files) + len(unknown_files)

        print(f"📁 Verification Results:")
        print(f"  - Calcifications folder: {len(calc_files):,} files")
        print(f"  - Masses folder: {len(mass_files):,} files")
        print(f"  - Unknown folder: {len(unknown_files):,} files")
        print(f"  - Total organized: {total_organized:,} files")

        # Success check
        if total_organized == 10237:
            print(f"🎉 SUCCESS: All 10,237 images successfully organized!")
            success = True
        else:
            print(f"⚠️  WARNING: Expected 10,237 images, got {total_organized:,}")
            success = False

        # Show samples
        print(f"\n📋 Sample files:")
        if calc_files:
            print(f"  Calc samples: {', '.join([f.name for f in calc_files[:3]])}")
        if mass_files:
            print(f"  Mass samples: {', '.join([f.name for f in mass_files[:3]])}")
        if unknown_files:
            print(f"  Unknown samples: {', '.join([f.name for f in unknown_files[:3]])}")

        return success, total_organized


def main():
    dataset_path = "/home/mdbasit_tezu_ernet_in/.cache/kagglehub/datasets/awsaf49/cbis-ddsm-breast-cancer-image-dataset/versions/1"

    try:
        organizer = CBISDDSMCorrectOrganizer(dataset_path)

        # Organize all images
        calc_moved, mass_moved, unknown_moved, errors = organizer.organize_all_images()

        # Verify results
        success, total_organized = organizer.verify_final_organization()

        if success:
            print(f"\n🎉 PERFECT! All 10,237 images successfully organized!")
            print(f"📊 Breakdown:")
            print(f"   - Calcifications: {calc_moved:,}")
            print(f"   - Masses: {mass_moved:,}")
            print(f"   - Unknown: {unknown_moved:,}")
        else:
            print(f"\n❌ ISSUE: Only {total_organized:,} out of 10,237 images organized")

        print(f"\n📁 Your organized images are in:")
        print(f"   - {organizer.calc_dir}")
        print(f"   - {organizer.mass_dir}")
        print(f"   - {organizer.unknown_dir}")

    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
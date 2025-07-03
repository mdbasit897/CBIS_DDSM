import os
import shutil
import pandas as pd
from pathlib import Path
import glob


class CBISDDSMFinalOrganizer:
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

        print(f"Created directories:")
        print(f"  - Calcifications: {self.calc_dir}")
        print(f"  - Masses: {self.mass_dir}")
        print(f"  - Unknown: {self.unknown_dir}")

    def load_dicom_info(self):
        """Load dicom_info.csv which contains the direct mapping"""
        dicom_info_path = self.csv_path / "dicom_info.csv"

        if not dicom_info_path.exists():
            raise FileNotFoundError(f"dicom_info.csv not found at {dicom_info_path}")

        print(f"Loading {dicom_info_path}")
        df = pd.read_csv(dicom_info_path)
        print(f"Loaded {len(df)} rows from dicom_info.csv")

        return df

    def create_image_mapping(self, dicom_df):
        """Create mapping from JPEG filename to category (calc/mass)"""
        image_mapping = {}

        for _, row in dicom_df.iterrows():
            # Get the image path and patient name
            image_path = row['image_path']
            patient_name = row['PatientName']

            # Skip if either is missing
            if pd.isna(image_path) or pd.isna(patient_name):
                continue

            # Extract filename from image path
            # image_path format: 'CBIS-DDSM/jpeg/SeriesInstanceUID/filename.jpg'
            filename = Path(image_path).name

            # Determine category from PatientName
            patient_name_lower = str(patient_name).lower()

            if 'calc' in patient_name_lower:
                category = 'calc'
            elif 'mass' in patient_name_lower:
                category = 'mass'
            else:
                category = 'unknown'

            image_mapping[filename] = {
                'category': category,
                'patient_name': patient_name,
                'image_path': image_path
            }

        return image_mapping

    def organize_images(self):
        """Organize images using the direct mapping from dicom_info.csv"""
        print("\n=== Starting Image Organization ===")

        # Load dicom info
        dicom_df = self.load_dicom_info()

        # Create image mapping
        print("Creating image mapping...")
        image_mapping = self.create_image_mapping(dicom_df)
        print(f"Created mapping for {len(image_mapping)} images")

        # Count categories
        calc_count = sum(1 for info in image_mapping.values() if info['category'] == 'calc')
        mass_count = sum(1 for info in image_mapping.values() if info['category'] == 'mass')
        unknown_count = sum(1 for info in image_mapping.values() if info['category'] == 'unknown')

        print(f"Mapping breakdown:")
        print(f"  - Calc: {calc_count}")
        print(f"  - Mass: {mass_count}")
        print(f"  - Unknown: {unknown_count}")

        # Find all JPEG files
        print("\nFinding JPEG files...")
        all_images = []
        for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
            all_images.extend(glob.glob(str(self.jpeg_path / "**" / ext), recursive=True))

        print(f"Found {len(all_images)} JPEG files")

        # Organize images
        calc_moved = 0
        mass_moved = 0
        unknown_moved = 0
        not_found = 0

        for img_path in all_images:
            img_path = Path(img_path)
            filename = img_path.name

            if filename in image_mapping:
                info = image_mapping[filename]
                category = info['category']

                if category == 'calc':
                    destination = self.calc_dir / filename
                    shutil.copy2(img_path, destination)
                    calc_moved += 1
                    if calc_moved <= 10:  # Show first 10 for verification
                        print(f"Calc: {filename} -> {info['patient_name']}")
                elif category == 'mass':
                    destination = self.mass_dir / filename
                    shutil.copy2(img_path, destination)
                    mass_moved += 1
                    if mass_moved <= 10:  # Show first 10 for verification
                        print(f"Mass: {filename} -> {info['patient_name']}")
                else:
                    destination = self.unknown_dir / filename
                    shutil.copy2(img_path, destination)
                    unknown_moved += 1
                    if unknown_moved <= 10:  # Show first 10 for verification
                        print(f"Unknown: {filename} -> {info['patient_name']}")
            else:
                # Image not found in mapping - this shouldn't happen
                destination = self.unknown_dir / filename
                shutil.copy2(img_path, destination)
                not_found += 1
                if not_found <= 10:  # Show first 10 for debugging
                    print(f"Not in mapping: {filename}")

        print(f"\n=== ORGANIZATION COMPLETE ===")
        print(f"Calcifications: {calc_moved}")
        print(f"Masses: {mass_moved}")
        print(f"Unknown/Other: {unknown_moved}")
        print(f"Not found in mapping: {not_found}")
        print(f"Total processed: {calc_moved + mass_moved + unknown_moved + not_found}")

        return {
            'calc_moved': calc_moved,
            'mass_moved': mass_moved,
            'unknown_moved': unknown_moved,
            'not_found': not_found
        }

    def verify_organization(self):
        """Verify the organization results"""
        print(f"\n=== VERIFICATION ===")

        calc_files = list(self.calc_dir.glob("*.jpg"))
        mass_files = list(self.mass_dir.glob("*.jpg"))
        unknown_files = list(self.unknown_dir.glob("*.jpg"))

        print(f"Files in calcifications folder: {len(calc_files)}")
        print(f"Files in masses folder: {len(mass_files)}")
        print(f"Files in unknown folder: {len(unknown_files)}")

        # Show sample files
        print(f"\nSample calcification files:")
        for f in calc_files[:5]:
            print(f"  {f.name}")

        print(f"\nSample mass files:")
        for f in mass_files[:5]:
            print(f"  {f.name}")

        if unknown_files:
            print(f"\nSample unknown files:")
            for f in unknown_files[:5]:
                print(f"  {f.name}")


def main():
    # Your dataset path
    dataset_path = "/home/mdbasit_tezu_ernet_in/.cache/kagglehub/datasets/awsaf49/cbis-ddsm-breast-cancer-image-dataset/versions/1"
    print("🚀 CBIS-DDSM Image Organizer (Final Version)")
    print("=" * 50)

    try:
        organizer = CBISDDSMFinalOrganizer(dataset_path)

        # Organize images
        results = organizer.organize_images()

        # Verify results
        organizer.verify_organization()

        print(f"\n✅ Organization successful!")
        print(f"Your images are now organized in: {organizer.base_path / 'organized'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
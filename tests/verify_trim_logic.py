import shutil
import sys
from pathlib import Path

from PIL import Image

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.commands.trim.image_ops import trim_image
from src.shared.image_ops import ImageValidationError


def test_trim_logic():
    test_dir = Path("tests/temp_trim_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    print("Running trim logic verification...")

    # Case 1: Consistent corners (All White)
    img1_path = test_dir / "consistent.png"
    img1 = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    # Add a blue square in the middle so it's not empty
    for x in range(40, 60):
        for y in range(40, 60):
            img1.putpixel((x, y), (0, 0, 255, 255))
    img1.save(img1_path)

    try:
        path, modified = trim_image(img1_path, margin=0)
        if modified:
            print("[PASS] Case 1: Consistent corners trimmed successfully.")
        else:
            print("[FAIL] Case 1: Expected trimming but none reported.")
    except Exception as e:
        print(f"[FAIL] Case 1: Failed with error: {e}")

    # Case 2: Inconsistent corners (2 White, 2 Black)
    img2_path = test_dir / "inconsistent.png"
    img2 = Image.new("RGBA", (100, 100), (255, 255, 255, 255))  # Default white
    # Make bottom corners black
    img2.putpixel((0, 99), (0, 0, 0, 255))
    img2.putpixel((99, 99), (0, 0, 0, 255))
    img2.save(img2_path)

    try:
        trim_image(img2_path, margin=0)
        print("[FAIL] Case 2: Should have failed but succeeded.")
    except ImageValidationError as e:
        print(f"[PASS] Case 2: Correctly failed with: {e}")
    except Exception as e:
        print(f"[FAIL] Case 2: Failed with unexpected error: {e}")

    # Case 3: 3 Matching corners (3 White, 1 Black)
    img3_path = test_dir / "partial.png"
    img3 = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    # Make bottom-right black
    img3.putpixel((99, 99), (0, 0, 0, 255))
    # Add content
    for x in range(40, 60):
        for y in range(40, 60):
            img3.putpixel((x, y), (0, 0, 255, 255))
    img3.save(img3_path)

    try:
        path, modified = trim_image(img3_path, margin=0)
        if modified:
            print("[PASS] Case 3: 3 matching corners trimmed successfully.")
        else:
            print("[FAIL] Case 3: Expected trimming but none reported.")
    except Exception as e:
        print(f"[FAIL] Case 3: Failed with error: {e}")

    # Case 4: No change (Already trimmed)
    # Re-trimming the trimmed image from Case 1
    img1_trimmed_path = test_dir / "consistent_trimmed.png"
    try:
        path, modified = trim_image(img1_trimmed_path, margin=0)
        if not modified:
            print("[PASS] Case 4: Correctly identified no changes needed.")
        else:
            print("[FAIL] Case 4: Reported modification when none should have occurred.")
    except Exception as e:
        print(f"[FAIL] Case 4: Failed with error: {e}")

    # Cleanup
    shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_trim_logic()

import shutil
import sys
from pathlib import Path

from PIL import Image

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.commands.manipulate.cli import _process_single_file, parse_operations


def test_manipulate_logic():
    test_dir = Path("tests/temp_manipulate_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    print("Running manipulate logic verification...")

    # Case 1: Parse operations
    try:
        ops = parse_operations("e,t48")
        assert ops == [("e", None), ("t", 48)]
        print("[PASS] Operation parsing successful.")
    except Exception as e:
        print(f"[FAIL] Operation parsing failed: {e}")

    # Case 2: Chain e,t48
    img_path = test_dir / "logo.png"
    # Create a 10x10 blue square with white background
    img = Image.new("RGB", (10, 10), (255, 255, 255))
    img.putpixel((5, 5), (0, 0, 255))
    img.save(img_path)

    try:
        # e -> 30x30, t48 -> should result in a 30x30 if margin is 48 (clamped to image size)
        # Actually t48 on a 30x30 image with a blue dot in the middle (at 15,15)
        # would try to add 48px margin around the dot, but it will be clamped to (0,0,30,30).
        # So size should be 30x30.
        status = _process_single_file(img_path, [("e", None), ("t", 48)], replace=False)
        output_path = test_dir / "logo_processed.png"

        with Image.open(output_path) as result:
            if result.size == (30, 30):
                print("[PASS] Case 2: Chain e,t48 executed correctly.")
            else:
                print(f"[FAIL] Case 2: Unexpected size {result.size}, expected (30, 30).")
    except Exception as e:
        print(f"[FAIL] Case 2: Failed with error: {e}")

    # Case 3: Trim only
    try:
        # Create a large white image with a small blue dot
        img2_path = test_dir / "to_trim.png"
        img2 = Image.new("RGB", (100, 100), (255, 255, 255))
        img2.putpixel((50, 50), (0, 0, 255))
        img2.save(img2_path)

        # Trim with margin 5 -> resulting size should be 1+5+5 = 11x11
        status = _process_single_file(img2_path, [("t", 5)], replace=False)
        output2_path = test_dir / "to_trim_processed.png"

        with Image.open(output2_path) as result:
            if result.size == (11, 11):
                print("[PASS] Case 3: Trim only executed correctly.")
            else:
                print(f"[FAIL] Case 3: Unexpected size {result.size}, expected (11, 11).")
    except Exception as e:
        print(f"[FAIL] Case 3: Failed with error: {e}")

    # Cleanup
    shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_manipulate_logic()

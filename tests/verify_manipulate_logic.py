import shutil
import sys
from pathlib import Path
from PIL import Image

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.commands.manipulate.cli import parse_operations, _process_single_file

def test_manipulate_logic():
    test_dir = Path("tests/temp_manipulate_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    print("Running manipulate logic verification...")

    # Case 1: Parse operations
    try:
        ops = parse_operations("e,t48")
        assert ops == [('e', None), ('t', 48)]
        print("[PASS] Operation parsing successful.")
    except Exception as e:
        print(f"[FAIL] Operation parsing failed: {e}")

    # Case 2: Chain e,t48
    img_path = test_dir / "logo.png"
    img = Image.new("RGB", (10, 10), (255, 255, 255))
    img.putpixel((5, 5), (0, 0, 255))
    img.save(img_path)

    try:
        status = _process_single_file(img_path, [('e', None), ('t', 48)], replace=False, skip_same=True)
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
        img2_path = test_dir / "to_trim.png"
        img2 = Image.new("RGB", (100, 100), (255, 255, 255))
        img2.putpixel((50, 50), (0, 0, 255))
        img2.save(img2_path)
        
        status = _process_single_file(img2_path, [('t', 5)], replace=False, skip_same=True)
        output2_path = test_dir / "to_trim_processed.png"
        
        with Image.open(output2_path) as result:
            if result.size == (11, 11):
                print("[PASS] Case 3: Trim only executed correctly.")
            else:
                print(f"[FAIL] Case 3: Unexpected size {result.size}, expected (11, 11).")
    except Exception as e:
        print(f"[FAIL] Case 3: Failed with error: {e}")

    # Case 4: Skip same (Already optimal)
    try:
        img3_path = test_dir / "already_trimmed.png"
        img3 = Image.new("RGB", (10, 10), (255, 255, 255))
        img3.putpixel((5, 5), (0, 0, 255))
        img3.save(img3_path)
        
        # Trim with margin 10 on a 10x10 image with content in middle 
        # should result in same size (clamped)
        status = _process_single_file(img3_path, [('t', 10)], replace=False, skip_same=True)
        if status == "no_change":
            print("[PASS] Case 4: Correctly identified no change for identical result.")
        else:
            print(f"[FAIL] Case 4: Expected 'no_change', got '{status}'.")
    except Exception as e:
        print(f"[FAIL] Case 4: Failed with error: {e}")

    # Cleanup
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_manipulate_logic()

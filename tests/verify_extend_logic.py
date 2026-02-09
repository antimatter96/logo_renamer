import shutil
import sys
from pathlib import Path

from PIL import Image

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.commands.extend.image_ops import extend_image


def test_extend_logic():
    test_dir = Path("tests/temp_extend_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    print("Running extend logic verification...")

    # Case 1: Simple RGB image (Blue square on white)
    img1_path = test_dir / "white_bg.png"
    # 10x10 image, white background
    img1 = Image.new("RGB", (10, 10), (255, 255, 255))
    # Blue pixel in the middle
    img1.putpixel((5, 5), (0, 0, 255))
    img1.save(img1_path)

    try:
        output_path = extend_image(img1_path, replace=False)
        with Image.open(output_path) as result:
            # Should be 30x30
            if result.size == (30, 30):
                # Center pixel should be blue
                # Original image starts at (10, 10), so (5, 5) becomes (15, 15)
                if result.getpixel((15, 15)) == (0, 0, 255):
                    # Edge pixel should be white
                    if result.getpixel((0, 0)) == (255, 255, 255):
                        print("[PASS] Case 1: RGB image extended and centered correctly.")
                    else:
                        print(
                            f"[FAIL] Case 1: Edge color is {result.getpixel((0, 0))}, expected white."
                        )
                else:
                    print(
                        f"[FAIL] Case 1: Center pixel color is {result.getpixel((15, 15))}, expected blue."
                    )
            else:
                print(f"[FAIL] Case 1: Unexpected size {result.size}, expected (30, 30).")
    except Exception as e:
        print(f"[FAIL] Case 1: Failed with error: {e}")

    # Case 2: RGBA image with transparency
    img2_path = test_dir / "transparent.png"
    # Transparent background (0, 0, 0, 0)
    img2 = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    # Red pixel in middle
    img2.putpixel((5, 5), (255, 0, 0, 255))
    img2.save(img2_path)

    try:
        output_path = extend_image(img2_path, replace=False)
        with Image.open(output_path) as result:
            if result.size == (30, 30):
                # Center pixel should be red
                if result.getpixel((15, 15)) == (255, 0, 0, 255):
                    # Edge pixel should be transparent
                    if result.getpixel((0, 0)) == (0, 0, 0, 0):
                        print("[PASS] Case 2: RGBA image extended and centered correctly.")
                    else:
                        print(
                            f"[FAIL] Case 2: Edge color is {result.getpixel((0, 0))}, expected transparent."
                        )
                else:
                    print(
                        f"[FAIL] Case 2: Center pixel color is {result.getpixel((15, 15))}, expected red."
                    )
            else:
                print(f"[FAIL] Case 2: Unexpected size {result.size}.")
    except Exception as e:
        print(f"[FAIL] Case 2: Failed with error: {e}")

    # Cleanup
    shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_extend_logic()

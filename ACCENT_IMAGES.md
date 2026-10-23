# Images that carry the accent

Written by `tools/accent_images.py` (#86 A). Do not edit by hand: after adding or changing an image, run `python tools/accent_images.py`. `tests/test_accent_images.py` fails until this file is what the tool writes.

If the accent ever moves, the code moves it in ten lines; these images do not move with it. **shaded** art is hand-made and is remade by hand (#84). **flat** art could be recolored by swapping exact colors. A **screenshot** is retaken. A **fixture** is a test input. Accent: hue within 6 degrees of `BRAND_GOLD` or `BRAND_DARK_GOLD`, saturation and value at least 0.15; an image carries it from 1% of its pixels; flat means its three commonest accent colors cover at least 90% of them. The tool's docstring says why.

**35 images of art carry the accent, 35 of them distinct.**

| folder | files | shaded | flat | screenshot | fixture | none |
|---|---|---|---|---|---|---|
| `resources/background_images` | 1 | 1 | 0 | 0 | 0 | 0 |
| `resources/button_images` | 30 | 30 | 0 | 0 | 0 | 0 |
| `resources/icons` | 4 | 4 | 0 | 0 | 0 | 0 |
| `resources/screenshots` | 6 | 0 | 0 | 6 | 0 | 0 |

## `resources/background_images`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `background.png` | 3840x2169 | 19.7% | 3006 | shaded |  |

## `resources/button_images`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `add_base.png` | 1250x146 | 30.4% | 2663 | shaded |  |
| `add_hover.png` | 1250x146 | 31.8% | 2663 | shaded |  |
| `add_pressed.png` | 1250x146 | 41.6% | 2663 | shaded |  |
| `clear-all_base.png` | 1250x146 | 30.8% | 2861 | shaded |  |
| `clear-all_hover.png` | 1250x146 | 32.5% | 2904 | shaded |  |
| `clear-all_pressed.png` | 1250x146 | 44.0% | 3320 | shaded |  |
| `clear_base.png` | 417x105 | 36.1% | 1555 | shaded |  |
| `clear_hover.png` | 417x105 | 41.2% | 1555 | shaded |  |
| `clear_pressed.png` | 417x105 | 45.4% | 1579 | shaded |  |
| `export_base.png` | 1250x146 | 35.6% | 2663 | shaded |  |
| `export_hover.png` | 1250x146 | 33.1% | 2663 | shaded |  |
| `export_pressed.png` | 1250x146 | 43.8% | 2663 | shaded |  |
| `import_base.png` | 1250x146 | 32.0% | 2883 | shaded |  |
| `import_hover.png` | 1250x146 | 33.4% | 2930 | shaded |  |
| `import_pressed.png` | 1250x146 | 42.2% | 2663 | shaded |  |
| `lock_base.png` | 417x105 | 32.2% | 1696 | shaded |  |
| `lock_hover.png` | 417x105 | 32.5% | 1696 | shaded |  |
| `lock_pressed.png` | 417x105 | 40.5% | 1699 | shaded |  |
| `reset_base.png` | 1250x146 | 31.4% | 2663 | shaded |  |
| `reset_hover.png` | 1250x146 | 31.6% | 2663 | shaded |  |
| `reset_pressed.png` | 1250x146 | 41.3% | 2553 | shaded |  |
| `save_base.png` | 1250x146 | 31.9% | 2663 | shaded |  |
| `save_hover.png` | 1250x146 | 32.2% | 2663 | shaded |  |
| `save_pressed.png` | 1250x146 | 42.3% | 2663 | shaded |  |
| `settings_gear_base.png` | 512x512 | 93.4% | 3390 | shaded |  |
| `settings_gear_hover.png` | 512x512 | 92.9% | 2888 | shaded |  |
| `settings_gear_pressed.png` | 512x512 | 93.1% | 3418 | shaded |  |
| `upload_base.png` | 417x105 | 34.2% | 1977 | shaded |  |
| `upload_hover.png` | 417x105 | 34.3% | 1889 | shaded |  |
| `upload_pressed.png` | 417x105 | 43.7% | 2124 | shaded |  |

## `resources/icons`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `app_icon.ico` | 256x256 | 81.5% | 1363 | shaded |  |
| `icon.ico` | 256x256 | 81.5% | 1363 | shaded |  |
| `icon.png` | 512x512 | 81.1% | 3602 | shaded |  |
| `special_slot.png` | 417x417 | 72.7% | 2041 | shaded |  |

## `resources/screenshots`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `about-dialog.png` | 1920x1080 | 19.2% | 9951 | screenshot |  |
| `batch-export.png` | 1920x1080 | 12.0% | 8939 | screenshot |  |
| `dark-mode.png` | 1920x1080 | 3.9% | 1959 | screenshot |  |
| `image-mode.png` | 1920x1080 | 21.7% | 9335 | screenshot |  |
| `light-mode.png` | 1920x1080 | 3.8% | 1967 | screenshot |  |
| `settings-dialog.png` | 1920x1080 | 11.5% | 10884 | screenshot |  |

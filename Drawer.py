from PIL import Image, ImageTk

cached_images = dict()


def ebc_to_color(ebc):
    # These values are on SRM scale, which is EBC divided by 2.
    colors = ["#FFE699",
              "#FFD878",
              "#FFCA5A",
              "#FFBF42",
              "#FBB123",
              "#F8A600",
              "#F39C00",
              "#EA8F00",
              "#E58500",
              "#DE7C00",
              "#D77200",
              "#CF6900",
              "#CB6200",
              "#C35900",
              "#BB5100",
              "#B54C00",
              "#B04500",
              "#A63E00",
              "#A13700",
              "#9B3200",
              "#952D00",
              "#8E2900",
              "#882300",
              "#821E00",
              "#7B1A00",
              "#771900",
              "#701400",
              "#6A0E00",
              "#660D00",
              "#5E0B00",
              "#5A0A02",
              "#560905",
              "#520907",
              "#4C0505",
              "#470606",
              "#440607",
              "#3F0708",
              "#3B0607",
              "#3A070B",
              "#36080A"]

    color_index = ebc // 2

    return colors[min(len(colors) - 1, max(color_index, 0))]


def color_to_rgb(color, brighten_by_percent: int = None):
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    if brighten_by_percent is not None:
        red = min(255, red + int((255 - red) * brighten_by_percent / 100))
        green = min(255, green + int((255 - green) * brighten_by_percent / 100))
        blue = min(255, blue + int((255 - blue) * brighten_by_percent / 100))
    return red, green, blue


def color_transparent_parts(img, color, region, override_color=None):
    for x in range(region[0], region[2]):
        for y in range(region[1], region[3]):
            r, g, b, a = img.getpixel((x, y))
            if a == 0:  # If the pixel is fully transparent
                img.putpixel((x, y), (*color, 255))  # Replace RGB with the desired color
            elif override_color is not None and (r, g, b) == override_color:
                img.putpixel((x, y), (*color, 255))  # Replace RGB with the desired color


def color_beer_image(ebc):
    if cached_images.get(ebc) is None:
        img = Image.open("beer.png")
        img = img.convert("RGBA")

        beer_color = color_to_rgb(ebc_to_color(ebc))
        foam_color = color_to_rgb(ebc_to_color(ebc), 65)

        # Color the beer
        # Specify the region (x1, y1, x2, y2) to color transparent parts
        region_beer = (66, 130, 238, 339)
        # Color the specified transparent parts in the image
        color_transparent_parts(img, beer_color, region_beer)

        # Color the foam
        region_foam = (66, 100, 238, 130)
        color_transparent_parts(img, foam_color, region_foam)
        region_foam = (55, 65, 250, 100)
        color_transparent_parts(img, foam_color, region_foam)
        region_foam = (85, 36, 219, 65)
        color_transparent_parts(img, foam_color, region_foam)
        region_foam = (130, 10, 175, 36)
        color_transparent_parts(img, foam_color, region_foam)
        region_foam = (90, 130, 120, 175)
        color_transparent_parts(img, foam_color, region_foam, override_color=beer_color)

        photo = ImageTk.PhotoImage(img)
        cached_images.setdefault(ebc, photo)
    return cached_images.get(ebc)

from PIL import Image

def main():
    image = Image.open("astronaut.png")
    image = image.crop((0, 0, 1024, 1024))
    image.save("astronaut_crop.png")
    
    # Convert the image to YCbCr color space
    image_ycbcr = image.convert("YCbCr")

    # Get the YCbCr channels
    y, cb, cr = image_ycbcr.split()

    # Create a new image with the Y channel set to a constant value of 128
    y_const = Image.new("L", image_ycbcr.size, 128)

    # Merge the constant Y channel with the original Cb and Cr channels
    image_without_y = Image.merge("YCbCr", (y_const, image_ycbcr.getchannel("Cb"), image_ycbcr.getchannel("Cr")))

    # Convert the image back to RGB color space
    image_rgb = image_without_y.convert("RGB")

    # Save the output image
    image_rgb.save("astronaut_without_y.png")
    
    # Extract the Y channel from the image
    y_channel = y

    # Create a new image with only the Y channel
    image_brightness = Image.merge("YCbCr", (y_channel, Image.new("L", image_ycbcr.size, 128), Image.new("L", image_ycbcr.size, 128)))

    # Convert the image back to RGB color space
    image_rgb = image_brightness.convert("RGB")

    # Save the output image
    image_rgb.save("astronaut_brightness.png")
    
    # Create a new image with only the Cr channel
    cr_image = Image.merge("YCbCr", (Image.new("L", cr.size, 128), Image.new("L", cr.size, 128),cr))
    
    # Save the new image
    cr_image.save("cr_only_image.jpg")
    
    # Create a new image with only the Cb channel
    cb_image = Image.merge("YCbCr", (Image.new("L", cr.size, 128), cb, Image.new("L", cr.size, 128)))
    
    cb_image.save("cb_only_image.jpg")
    
if __name__ == "__main__":
    print("start...")
    main()
    print("end...")
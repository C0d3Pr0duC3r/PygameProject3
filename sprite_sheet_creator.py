from PIL import Image
import os

# Directory containing individual frame images
input_directory = "C:\\Users\\chris\\Documents\\Blender\\Exports\\Script_Test\\"

# Number of frames in sprite animation
num_frames = 100

# Initialize list to hold individual frames
frames = []

# Load each frame into memory
for frame in range(1, num_frames + 1):
    image_path = os.path.join(input_directory, f"image_{frame}.png")
    if os.path.exists(image_path):
        frames.append(Image.open(image_path))

# Determine sprite sheet dimensions
if frames:
    frame_width, frame_height = frames[0].size
    sprite_sheet_width = frame_width * len(frames)
    sprite_sheet_height = frame_height

    # Create a new image for sprite sheet
    sprite_sheet = Image.new("RGBA", (sprite_sheet_width, sprite_sheet_height))

    # Paste each frame into sprite sheet
    for index, frame in enumerate(frames):
        position = (index * frame_width, 0)
        sprite_sheet.paste(frame, position)

    # Save sprite sheet
    sprite_sheet_path = os.path.join(input_directory, "missile_launcher_model.png")
    sprite_sheet.save(sprite_sheet_path)

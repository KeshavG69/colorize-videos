import os
import utils
from generator import Generator
import torch
from dataloaders import Colorization, datalaoder
import numpy as np
from PIL import Image
import subprocess


device = "cuda" if torch.cuda.is_available() else "cpu"

output_folder = "Frames"
video_path = "Indian_Village.mp4"
audio_path="Indian_Village.mp3"
video_url = "https://www.youtube.com/watch?v=Ydiz1Hzfx5s"

utils.download_yt_file(
    video_url=video_url, video_save_path=video_path, audio_save_path=audio_path
)

if not os.path.exists(output_folder):
    os.makedirs(output_folder)



subprocess.run("ffmpeg -i Indian_Village.mp4 -vf fps=30 Frames/frame-%04d.png", shell=True, capture_output=True, text=True)

frames = utils.get_file_path(output_folder)

frames = sorted(frames, key=utils.get_frame_number)

frames_dataset = Colorization(frames, size=256, split="test")

frames_dataloader = datalaoder(dataset=frames_dataset, BATCH_SIZE=32, shuffle=False)

gen = Generator(in_channels=1).to(device)

gen.load_state_dict(
    torch.load(
        "gen_model_30_face_25_landscape.pth",
        map_location=torch.device(device),
    )
)

gen.eval()

fake_images = []  # List to store generated fake RGB images
real_images = []  # List to store real RGB images
for idx, batch in enumerate(
    frames_dataloader
):  # Assuming your data loader yields batches of L and AB channels
    print(idx)
    L = batch["L"].to(device)
    ab = batch["ab"].to(device)
    fake_color = gen(L)  # Generate fake color predictions
    real_color = ab
    fake_image = utils.lab_to_rgb(L, fake_color)  # Convert fake color to RGB
    real_image = utils.lab_to_rgb(L, real_color)
    fake_images.append(fake_image)  # Append fake RGB image to list
    real_images.append(real_image)

fake_images = np.vstack(fake_images)
real_images = np.vstack(real_images)

output_dir = "Coloured_Frames"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

fake_images_uint8 = (fake_images * 255).astype(np.uint8)

for i, img in enumerate(fake_images_uint8):
    # Create the filename with leading zeros
    filename = f"{i+1:04}.jpg"
    filepath = os.path.join(output_dir, filename)

    # Convert the NumPy array to a PIL Image and save it
    image = Image.fromarray(img)
    image.save(filepath)

    print(f"Saved {filepath}")

subprocess.run("fffmpeg -framerate 30 -i Coloured_Frames/%04d.jpg -i Indian_Village.mp3 -c:v libx264 -c:a aac -r 30 -pix_fmt yuv420p -shortest output_video.mp4", shell=True, capture_output=True, text=True)



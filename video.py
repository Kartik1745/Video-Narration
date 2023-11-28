from IPython.display import Audio
from pathlib import Path
import cv2
import base64
from openai import OpenAI
import os
import requests
from openai import OpenAI
import pygame
from moviepy.editor import VideoFileClip, AudioFileClip

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key = api_key)
video_path = './wildlife.mp4'

output_path = './frames'

interval_seconds = 30

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video.")
    quit()

if not os.path.exists(output_path):
    os.makedirs(output_path)

frame_count = 0
interval_frames = int(cap.get(cv2.CAP_PROP_FPS) * interval_seconds)

print(f"Converting video to frames.")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    if frame_count % interval_frames == 0:
        frame_path = os.path.join(output_path, f'frame_{frame_count // interval_frames}.png')
        cv2.imwrite(frame_path, frame)

    frame_count += 1

cap.release()

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def generate_voiceover_script(folder_path):
    print("generating voiceover script")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    base64_image = encode_image(image_path)

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "These are frames of a video. Create a short voiceover script in the style of David Attenborough. Only include the narration."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 100
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    script = response.json()['choices'][0]['message']['content']

    return script

def generate_audio(script):
    print("generating audio")
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=script
    )
    response.stream_to_file(speech_file_path)
    return speech_file_path

folder_path = "./frames"

for file in os.listdir(folder_path):
    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
        image_path = os.path.join(folder_path, file)
        voiceover_script = generate_voiceover_script(image_path)
        speech_file_path = generate_audio(voiceover_script)
        if speech_file_path.exists():
            pygame.mixer.init()
            pygame.mixer.music.load(speech_file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                continue


# Write the final video with attached audio

video_path = "./wildlife.mp4"
audio_path = "./speech.mp3"

output_path = "./output.mp4"

video_clip = VideoFileClip(video_path)
audio_clip = AudioFileClip(audio_path)

video_clip = video_clip.set_audio(audio_clip)

video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

video_clip.close()
audio_clip.close()
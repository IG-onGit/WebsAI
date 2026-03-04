from imports import *


class Gemini:
    ####################################################################################// Params
    api_key = ""
    model = ""
    client = None

    ####################################################################################// Load
    def __init__(self, key, model):
        Gemini.api_key = key
        Gemini.model = model
        Gemini.client = genai.Client()
        pass

    ####################################################################################// Main
    def message(prompt):
        response = Gemini.client.models.generate_content(
            model=Gemini.model, contents=prompt
        )

        return response.text

    def code(prompt):
        resp = Gemini.client.models.generate_content(
            model=Gemini.model, contents=prompt
        )
        text = resp.text
        files = []
        current_file = None
        buffer = []

        for line in text.splitlines():
            if line.startswith("```"):
                if current_file is None:
                    current_file = "code"
                    buffer = []
                else:
                    files.append({current_file: "\n".join(buffer)})
                    current_file = None
            else:
                if current_file is not None:
                    buffer.append(line)

        return files

    def image(prompt, path):
        try:
            response = Gemini.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1),
            )
            image_data = response.generated_images[0].image

            with open(path, "wb") as f:
                f.write(image_data)
            return path
        except Exception:
            return ""
        return ""

    def video(prompt, path):
        try:
            op = Gemini.client.models.generate_videos(
                model="veo-3.1-generate-preview", prompt=prompt
            )

            while not op.done:
                time.sleep(2)
                op = Gemini.client.operations.get(op)

            video_data = op.response.generated_videos[0].video
            with open(path, "wb") as f:
                f.write(video_data)
            return path
        except Exception:
            return ""
        return ""

    def audio(prompt, path):
        try:
            response = Gemini.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Kore"
                            )
                        )
                    ),
                ),
            )

            pcm_data = response.candidates[0].content.parts[0].inline_data.data
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(pcm_data)
            return path
        except Exception:
            return ""
        return ""

    ####################################################################################// Helpers

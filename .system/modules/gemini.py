from imports import *


class Gemini:
    ####################################################################################// Params
    model = ""
    client = None
    location = "us-central1"

    ####################################################################################// Load
    def __init__(self, key, model, project):
        file = os.path.join(project, key)
        account = json.loads(cli.read(file))

        creds = service_account.Credentials.from_service_account_file(file)
        scoped_creds = creds.with_scopes(
            ["https://www.googleapis.com/auth/cloud-platform"]
        )

        Gemini.model = model
        Gemini.client = genai.Client(
            vertexai=True,
            project=account["project_id"],
            location=Gemini.location,
            credentials=scoped_creds,
        )

        pass

    ####################################################################################// Main
    def message(prompt):
        response = Gemini.client.models.generate_content(
            model=Gemini.model, contents=prompt
        )

        return response.text

    def code(prompt):
        files = {}

        try:
            resp = Gemini.client.models.generate_content(
                model=Gemini.model, contents=prompt
            )
            pattern = r"\d+\.\s+([^\n]+)\s*\n```(?:[a-zA-Z0-9]+)?\n(.*?)```"
            matches = re.findall(pattern, resp.text, re.DOTALL)

            for filename, content in matches:
                files[filename.strip()] = content.replace("—", "-").strip()
            return files
        except Exception:
            return {}
        return {}

    def image(prompt, path):
        try:
            response = Gemini.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1),
            )
            image_data = response.generated_images[0].image.image_bytes

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

            video_data = op.response.generated_videos[0].video.video_bytes

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

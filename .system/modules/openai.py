from imports import *


class Openai:
    ####################################################################################// Params

    ####################################################################################// Load
    def __init__(self, key, model, project):
        Openai.model = model
        Openai.client = OpenAIClient(api_key=key)
        pass

    ####################################################################################// Main
    def message(prompt):
        try:
            response = Openai.client.responses.create(model=Openai.model, input=prompt)
            return response.output_text.replace("—", "-")
        except Exception as e:
            return str(e)
        return ""

    def code(prompt):
        files = {}

        try:
            response = Openai.client.responses.create(model=Openai.model, input=prompt)
            text = response.output_text
            pattern = r"\d+\.\s+([^\n]+)\s*\n```(?:[a-zA-Z0-9]+)?\n(.*?)```"
            matches = re.findall(pattern, text, re.DOTALL)

            for filename, content in matches:
                files[filename.strip()] = content.replace("—", "-").strip()
            return files
        except Exception:
            return {}
        return {}

    def image(prompt, path):
        try:
            result = Openai.client.images.generate(
                model="gpt-image-1", prompt=prompt, size="1024x1024"
            )
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)

            with open(path, "wb") as f:
                f.write(image_bytes)
            return path
        except Exception:
            return ""
        return ""

    def video(prompt, path):
        # Not available via stable API
        return ""

    def audio(prompt, path):
        try:
            result = Openai.client.audio.speech.create(
                model="gpt-4o-mini-tts", voice="alloy", input=prompt
            )

            with open(path, "wb") as f:
                f.write(result.read())

            return path
        except Exception:
            return ""
        return ""

    ####################################################################################// Helpers

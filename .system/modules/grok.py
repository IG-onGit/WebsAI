from imports import *


class Grok:
    ####################################################################################// Params
    key = ""
    model = ""
    base_url = ""

    ####################################################################################// Load
    def __init__(Grok, key, model, project):
        Grok.key = key
        Grok.model = model
        Grok.base_url = "https://api.x.ai/v1"
        pass

    ####################################################################################// Main
    def message(prompt):
        url = f"{Grok.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {Grok.key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": Grok.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        try:
            r = requests.post(url, headers=headers, json=data)
            if r.status_code != 200:
                return ""
            result = r.json()
            return result["choices"][0]["message"]["content"]
        except:
            return ""
        return ""

    def code(prompt):
        text = Grok.message(prompt)
        if not text:
            return {}

        files = {}
        pattern = r"```(?:[a-zA-Z0-9]+)?\s*([^\n]*)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)

        for m in matches:
            filename = m[0].strip()
            code = m[1]
            if filename == "":
                filename = f"file_{len(files)+1}.txt"
            files[filename] = code.strip()
        return files

    def image(prompt, path):
        url = f"{Grok.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {Grok.key}",
            "Content-Type": "application/json",
        }
        data = {"model": "grok-2-image", "prompt": prompt, "size": "1024x1024"}

        try:
            r = requests.post(url, headers=headers, json=data)
            if r.status_code != 200:
                return ""

            result = r.json()
            image_url = result["data"][0]["url"]
            image_data = requests.get(image_url).content
            filename = f"grok_image_{int(time.time())}.png"

            with open(filename, "wb") as f:
                f.write(image_data)
            return filename
        except:
            return ""
        return ""

    def video(prompt, path):
        # Currently unsupported
        return ""

    def audio(prompt, path):
        # Currently unsupported
        return ""

    ####################################################################################// Helpers

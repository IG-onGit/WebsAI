from imports import *


class Claude:
    ####################################################################################// Params
    client = None
    model = None

    ####################################################################################// Load
    def __init__(self, key, model):
        Claude.client = Anthropic(api_key=key)
        Claude.model = model
        pass

    ####################################################################################// Main
    def message(prompt):
        if not Claude.client:
            return ""

        try:
            response = Claude.client.messages.create(
                model=Claude.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            text = ""
            for block in response.content:
                if block.type == "text":
                    text += block.text
            return text.strip()
        except Exception:
            return ""
        return ""

    def code(prompt):
        if not Claude.client:
            return {}

        try:
            response = Claude.client.messages.create(
                model=Claude.model,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )

            text = ""
            for block in response.content:
                if block.type == "text":
                    text += block.text

            files = {}
            pattern = r"```([a-zA-Z0-9]*)\s*([\s\S]*?)```"
            matches = re.findall(pattern, text)

            for i, match in enumerate(matches):
                language = match[0].strip()
                code = match[1].strip()
                filename = None
                first_line = code.split("\n")[0]
                file_match = re.search(
                    r"(?:file:|filename:|path:)\s*([^\s]+)", first_line, re.IGNORECASE
                )

                if file_match:
                    filename = file_match.group(1)
                if not filename:
                    ext = language if language else "txt"
                    filename = f"file_{i}.{ext}"

                files[filename] = code

            return files
        except Exception:
            return {}
        return {}

    def image(prompt, path):
        # Not supported by Claude API
        return ""

    def video(prompt, path):
        # Not supported by Claude API
        return ""

    def audio(prompt, path):
        # Not supported by Claude API
        return ""

    ####################################################################################// Helpers

from imports import *


class index:
    ####################################################################################// Load
    def __init__(self, app="", cwd="", args=[]):
        self.app, self.cwd, self.args = app, cwd, args
        # ...
        cli.dev = "-trace" in args
        self.stopped = False

        Patch("./")
        pass

    def __exit__(self):
        if not self.stopped:
            self.stop()
            DB.close()
        pass

    ####################################################################################// Main
    def new(self, cmd=""):  # Create new project
        if self.__getEnv("websai_local").strip() != "":
            return "Project already created"

        frame = os.path.join(self.app, ".system/frame")
        if not os.path.exists(frame):
            return f"Frame directory '{frame}' does not exist!"

        utc_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for root, dirs, files in os.walk(frame):
            rel_path = os.path.relpath(root, frame)
            target_dir = os.path.join(self.cwd, rel_path)
            os.makedirs(target_dir, exist_ok=True)

            values = {}
            for file_name in files:
                src_file = os.path.join(root, file_name)
                dest_file = os.path.join(target_dir, file_name)

                try:
                    with open(src_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    is_text = True
                except UnicodeDecodeError:
                    is_text = False

                if is_text:
                    keys = re.findall(r"\{\{(.*?)\}\}", content)
                    for key in keys:
                        if key not in values:
                            values[key] = cli.input(self.__textify(key), True)
                    for key, val in values.items():
                        content = content.replace(f"{{{{{key}}}}}", val)
                    content = content.replace("<date_time>", utc_date)
                    cli.write(dest_file, content)
                else:
                    shutil.copy2(src_file, dest_file)

        config = os.path.join(self.cwd, ".htaccess")
        os.rename(os.path.join(self.cwd, "-htaccess"), config)

        if os.path.exists(config):
            content = cli.read(config)
            content = content.replace("<database_pass>", cli.input("Database pass"))
            print()
            content = content.replace(
                "<ai_model>",
                cli.selection(
                    "Set AI Model",
                    [
                        "openai/gpt-5.2",
                        "openai/gpt-5-mini",
                        "openai/gpt-5-nano",
                        "openai/gpt-4.1",
                        "openai/gpt-4.1-mini",
                        #
                        # NOW - Test and fix claude API
                        # "claude/claude-opus-4-6",
                        # "claude/claude-sonnet-4-6",
                        # "claude/claude-haiku-4-5",
                        #
                        # NOW - Test and fix gemini API
                        "gemini/gemini-2.5-pro",
                        "gemini/gemini-2.5-flash",
                        #
                        # NOW - Test and fix grok API
                        # "grok/grok-4-1-fast-reasoning",
                        # "grok/grok-4-1-fast-non-reasoning",
                        # "grok/grok-4",
                        # "grok/grok-code-fast-1",
                        # "grok/grok-beta",
                        #
                        # "",
                    ],
                    True,
                ),
            )
            content = content.replace("<ai_key>", cli.input("API Key", True))
            cli.write(config, content)
        print()

        if cli.selection("Want to start development?", ["Yes", "No"], True) == "Yes":
            return self.start()

        return "Project created"

    def start(self, cmd=""):  # Start project development
        domain = self.__getEnv("websai_local").strip()
        if not domain:
            return "Project not verified!"

        hint = "_".join(domain.split(".")[:-1]).lower().strip()
        if not Localhost.start("websai_" + hint, domain, True, self.app, self.cwd):
            cli.error("Localhost failed")
            return False

        Engine(self.app, self.cwd, self.__getEnv("db_name", hint + "_db"))
        DB(
            self.__getEnv("db_host"),
            self.__getEnv("db_name"),
            self.__getEnv("db_user"),
            self.__getEnv("db_pass"),
        )
        DB.new(Engine.database)

        cli.line("", "-")
        print()

        option = ""
        task = ""

        while True:
            options = {
                "Create page": "create",
                "Enhance page": "enhance",
                "Degrade page": "remove",
                "Fix issue": "fix",
                "[Exit]": "exit",
            }

            if not self.__developmentStarted():
                options = {"Generate project": "complete", **options}

            if not option:
                option = cli.selection("New request", list(options.keys()), True)

            if options[option] == "exit":
                self.stop()
                DB.close()
                print()
                sys.exit()

            if task:
                task += ".\n" + self.__message("Adjust")
            else:
                task = self.__message("Describe", True)
            print()

            model = self.__getEnv("websai_aimodel")
            key = self.__getEnv("websai_aikey")

            if not model:
                cli.error("Could not detect the model")

            if not Engine.generate(key, model, options[option], task):
                cli.error("Could not complete the task")

            confirm = cli.selection(
                "Want to keep changes?", ["Yes", "Redo", "No"], True
            )

            if confirm == "Yes":
                Engine.confirm()
            elif confirm == "Redo":
                Engine.rollback()
                continue
            elif confirm == "No":
                Engine.rollback()

            option = ""
            task = ""
        pass

    def stop(self, cmd=""):  # Stop localhost if didn't by itself
        domain = self.__getEnv("websai_local").strip()
        if not domain:
            return "Project not verified!"

        cli.info("Please wait ...")
        hint = "_".join(domain.split(".")[:-1]).lower().strip()
        Localhost.stop("websai_" + hint, domain, self.app, self.cwd)
        self.stopped = True
        pass

    ####################################################################################// Helpers
    def __getEnv(self, name="", default=""):
        if not name.strip():
            cli.error("Invalid environment variable name")
            return default

        file = self.cwd + "/.htaccess"
        if not os.path.exists(file):
            cli.trace("Could not find the configuration")
            return default

        pattern = re.compile(r"^\s*SetEnv\s+(\S+)\s+(.+?)\s*$")
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line)
                if match:
                    env_key, value = match.groups()
                    if env_key.lower().strip() == name.lower().strip():
                        value = value.strip().strip('"').strip("'")
                        return value

        return default

    def __textify(self, text):
        text = text.replace("_", " ")

        return text.capitalize()

    def __developmentStarted(self):
        pages = self.__getProjectPages()

        return len(pages) > 0

    def __getProjectPages(self):
        groups = os.listdir(self.cwd)
        if not groups:
            return ""

        skip = [
            ".",
            "..",
            ".git",
            ".env",
            ".vscode",
            "vendor",
            "assets",
            ".github",
            ".gitlab",
            ".gitignore",
            ".htaccess",
            "groups.php",
            "index.php",
            "LICENSE",
            "README.md",
            "robots.txt",
            "sitemap.xml",
            "composer.json",
            "composer.lock",
            # "",
        ]

        collect = []
        for group in groups:
            if not group or group in skip:
                continue
            path = os.path.join(self.cwd, group)
            if not os.path.isdir(path):
                continue
            for page in os.listdir(path):
                if not page or page in skip:
                    continue
                if group == "public" and page == "websai":
                    continue
                collect.append(f"{group}/{page}")

        return collect

    def __message(self, hint="", must=False):
        message = cli.input(hint, must)
        if os.path.isfile(message) and os.path.exists(message):
            cli.trace("Loading file: " + message)
            message = cli.read(message)

        return message

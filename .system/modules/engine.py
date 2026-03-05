from imports import *


class Engine:
    app = ""
    project = ""
    database = ""
    page = ""
    handler = None

    ####################################################################################// Load
    def __init__(self, app_folder, project_folder, project_database):
        Engine.app = app_folder
        Engine.project = project_folder
        Engine.database = project_database
        pass

    ####################################################################################// Main
    def generate(key, model, category, task):
        Engine.page = ""
        Engine.handler = None

        if not key:
            cli.error("AI key not specified")
            return False
        if not model:
            cli.error("AI model not specified")
            return False
        if category not in ["complete", "create", "enhance", "fix", "remove"]:
            cli.error("Invalid category")
            return False
        if not task:
            cli.error("Task not specified")
            return False

        if "/" in model:
            provider_name, model_name = model.split("/", 1)
        else:
            cli.error("Invalid model format. Expected provider/model")
            return False

        try:
            ProviderClass = globals()[provider_name.capitalize()]
        except KeyError:
            cli.error(f"Provider class '{provider_name}' not found")
            return False

        obj = Engine(Engine.app, Engine.project, Engine.database)
        Engine.handler = ProviderClass(key, model_name)
        prompt_func_name = f"__{category}__"
        prompt_func = getattr(obj, prompt_func_name, None)

        if not prompt_func:
            cli.error(f"Prompt function '{prompt_func_name}' not found")
            return False

        cli.setLoad(4, model)
        prompt = prompt_func(task)

        if not prompt:
            cli.error(f"Prompt for category '{category}' is empty")
            cli.endLoad()
            return False
        time.sleep(0.5)
        cli.addLoad(random.uniform(0.5, 1))

        time.sleep(0.5)
        Patch.new()

        action_func_name = f"_{category}_"
        action = getattr(obj, action_func_name, None)
        time.sleep(0.5)
        cli.addLoad(random.uniform(0.5, 1))

        if not action:
            Patch.rollback()
            cli.error(f"Action function '{action_func_name}' not found")
            cli.endLoad()
            return False
        time.sleep(0.5)
        cli.addLoad(random.uniform(0.5, 1))

        if not action(prompt):
            Patch.rollback()
            cli.error("Action execution failed")
            cli.endLoad()
            return False
        cli.endLoad()

        return True

    def rollback():
        Engine.page = ""
        Engine.handler = None
        Patch.rollback()
        pass

    def confirm():
        Engine.page = ""
        Engine.handler = None
        Patch.confirm()
        pass

    ####################################################################################// Actions
    def _complete_(self, prompt):
        pages = Engine.handler.__class__.code(prompt)

        cli.setLoad(len(pages), "Generating pages")
        for each in pages:
            parts = each.split(".")
            if len(parts) != 3:
                cli.addLoad(1)
                continue
            group, page, extension = parts
            if (
                not group
                or not page
                or page in ["README", "readme"]
                or extension != "md"
            ):
                cli.addLoad(1)
                continue
            desc = self.__page__(
                "Create new page, here is the description:\n\n" + pages[each]
            )
            self._page_(desc, group, page)
            cli.addLoad(1)
        cli.endLoad()

        if "README.md" in pages and pages["README.md"].strip() != "":
            Patch.add(Engine.project + "/README.md")
            cli.write(Engine.project + "/README.md", pages["README.md"])

        if "db.sql" in pages and pages["db.sql"].strip() != "":
            sql_file = os.path.join(Engine.project, "db.sql")
            cli.write(sql_file, pages["db.sql"])
            cli.command("code " + sql_file, False, True)
            if cli.selection("Confirm to update database", ["Go", "No"], True) == "Go":
                cli.trace("Updating database")
                DB.submit(pages["db.sql"])
            os.remove(sql_file)

        return True

    def _page_(self, prompt, group, page):
        code = Engine.handler.__class__.code(prompt)

        return self.__codeEditor(group, page, code)

    def _create_(self, prompt):
        code = Engine.handler.__class__.code(prompt)

        config = json.loads(code.get("config.json", "{}"))
        page_group = config.get("page-group", "group")
        page_name = config.get("page-name", "page")

        return self.__codeEditor(page_group, page_name, code)

    def _enhance_(self, prompt):
        parts = Engine.page.split("/")
        if len(parts) != 2:
            return False

        Engine.page = ""
        code = Engine.handler.__class__.code(prompt)

        return self.__codeEditor(parts[0], parts[1], code)

    def _fix_(self, prompt):
        parts = Engine.page.split("/")
        if len(parts) != 2:
            return False

        Engine.page = ""
        code = Engine.handler.__class__.code(prompt)

        return self.__codeEditor(parts[0], parts[1], code)

    def _remove_(self, prompt):
        parts = Engine.page.split("/")
        if len(parts) != 2:
            return False

        Engine.page = ""
        code = Engine.handler.__class__.code(prompt)

        return self.__codeEditor(parts[0], parts[1], code)

    ####################################################################################// Prompts
    def __complete__(self, task):
        base = self.__loadPrompt("complete-project")
        if not base:
            cli.error("Empty base prompt")
            return ""

        return self.__prompt(base, {"message": task})

    def __page__(self, task):
        base = self.__loadPrompt("complete-page")
        if not base:
            cli.error("Empty base prompt")
            return ""

        styling = ""
        pages = self.__getProjectPages(True)

        if "public/websai" in pages:
            pages.remove("public/websai")

        if len(pages) > 0:
            file = f"{Engine.project}/{pages[0]}/style.css"
            if os.path.exists(file):
                styling = cli.read(file)

        if styling.strip() == "":
            styling = "Styling not provided."

        files = []
        for page in pages:
            paths = self.__getFolderFiles(page)
            if len(paths) > 0:
                files.append(page + ":")
            for file in paths:
                files.append(f" - {file}")
            if len(paths) > 0:
                files.append("")
        files = "\n".join(files)

        schema = DB.schema()
        if schema.strip() == "":
            schema = "Schema not provided."

        return self.__prompt(
            base,
            {
                "database_schema": schema,
                "files": files,
                "styling": styling,
                "message": task,
            },
        )

    def __create__(self, task):
        base = self.__loadPrompt("create-page")
        if not base:
            cli.error("Empty base prompt")
            return ""

        styling = ""
        pages = self.__getProjectPages(True)
        example = cli.selection("Select styling example", pages)

        if example:
            file = f"{Engine.project}/{example}/style.css"
            if os.path.exists(file):
                styling = cli.read(file)

        if styling.strip() == "":
            styling = "Styling not provided."

        files = []
        for page in pages:
            paths = self.__getFolderFiles(page)
            if len(paths) > 0:
                files.append(page + ":")
            for file in paths:
                files.append(f" - {file}")
            if len(paths) > 0:
                files.append("")
        files = "\n".join(files)

        schema = DB.schema()
        if schema.strip() == "":
            schema = "Schema not provided."

        return self.__prompt(
            base,
            {
                "database_schema": schema,
                "files": files,
                "styling": styling,
                "message": task,
            },
        )

    def __enhance__(self, task):
        base = self.__loadPrompt("enhance-page")
        if not base:
            cli.error("Empty base prompt")
            return ""

        files = []
        pages = self.__getProjectPages(True)
        Engine.page = cli.selection("Select group page", pages, True)

        for page in pages:
            paths = self.__getFolderFiles(page)
            if len(paths) > 0:
                files.append(page + ":")
            for file in paths:
                files.append(f" - {file}")
            if len(paths) > 0:
                files.append("")
        files = "\n".join(files)

        schema = DB.schema()
        if schema.strip() == "":
            schema = "Schema not provided."

        code = self.__getCodeBase(f"{Engine.project}/{Engine.page}")
        if code.strip() == "":
            code = "Code base not provided."

        return self.__prompt(
            base,
            {
                "database_schema": schema,
                "files": files,
                "code_base": code,
                "message": task,
            },
        )

    def __fix__(self, task):
        base = self.__loadPrompt("fix-page")
        if not base:
            cli.error("Empty base prompt")
            return ""

        files = []
        pages = self.__getProjectPages(True)
        Engine.page = cli.selection("Select group page", pages, True)

        for page in pages:
            paths = self.__getFolderFiles(page)
            if len(paths) > 0:
                files.append(page + ":")
            for file in paths:
                files.append(f" - {file}")
            if len(paths) > 0:
                files.append("")
        files = "\n".join(files)

        schema = DB.schema()
        if schema.strip() == "":
            schema = "Schema not provided."

        code = self.__getCodeBase(f"{Engine.project}/{Engine.page}")
        if code.strip() == "":
            code = "Code base not provided."

        return self.__prompt(
            base,
            {
                "database_schema": schema,
                "files": files,
                "code_base": code,
                "message": task,
            },
        )

    def __remove__(self, task):
        base = self.__loadPrompt("remove-feature")
        if not base:
            cli.error("Empty base prompt")
            return ""

        files = []
        pages = self.__getProjectPages(True)
        Engine.page = cli.selection("Select group page", pages, True)

        for page in pages:
            paths = self.__getFolderFiles(page)
            if len(paths) > 0:
                files.append(page + ":")
            for file in paths:
                files.append(f" - {file}")
            if len(paths) > 0:
                files.append("")
        files = "\n".join(files)

        schema = DB.schema()
        if schema.strip() == "":
            schema = "Schema not provided."

        code = self.__getCodeBase(f"{Engine.project}/{Engine.page}")
        if code.strip() == "":
            code = "Code base not provided."

        return self.__prompt(
            base,
            {
                "database_schema": schema,
                "files": files,
                "code_base": code,
                "message": task,
            },
        )

    def __create_group__(self, name, description):
        base = self.__loadPrompt("create-group")
        if not base:
            cli.error("Empty base prompt")
            return ""

        schema = DB.schema()
        if schema.strip() == "":
            schema = "Schema not provided."

        pages = self.__getProjectPages()
        if pages.strip() == "":
            pages = "Pages not provided."

        return self.__prompt(
            base,
            {
                "name": name,
                "description": description,
                "database_schema": schema,
                "project_pages": pages,
            },
        )

    ####################################################################################// Helpers
    def __prompt(self, base, data):
        for key in data:
            base = base.replace("[[" + key + "]]", data[key])

        return base

    def __loadPrompt(self, name):
        try:
            return cli.read(f"{Engine.app}/.system/prompts/{name}.md")
        except FileNotFoundError:
            cli.error(f"Prompt file not found: {name}.md")
            return ""
        return ""

    def __groupMethodExists(self, name):
        file = os.path.join(Engine.project, "groups.php")
        if not os.path.exists(file):
            return False

        content = cli.read(file)
        pattern = rf"public\s+static\s+function\s+{re.escape(name)}\s*\("

        return re.search(pattern, content) is not None

    def __addGroupMethod(self, method):
        file = os.path.join(Engine.project, "groups.php")
        if not os.path.exists(file):
            return False

        content = cli.read(file)
        pos = content.rfind("}")

        if pos == -1:
            return False

        method = textwrap.dedent(method).strip("\n")
        lines = method.split("\n")
        formatted = "\n".join("    " + line if line else "" for line in lines)
        insertion = "\n" + formatted + "\n"
        new_content = content[:pos] + insertion + content[pos:]

        Patch.add(file)
        cli.write(file, new_content)

        return True

    def __getProjectPages(self, array=False):
        groups = os.listdir(Engine.project)
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
            path = os.path.join(Engine.project, group)
            if not os.path.isdir(path):
                continue
            for page in os.listdir(path):
                if not page or page in skip:
                    continue
                collect.append(f"{group}/{page}")

        if array:
            return collect

        return "\n".join(collect)

    def __getFolderFiles(self, folder):
        folder = os.path.join(Engine.project, folder)
        file_paths = []

        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, folder)
                file_paths.append(relative_path)

        return file_paths

    def __extractEnvVars(self, content):
        pattern = r"""App::env\(\s*      # App::env(
                      ['"]                # opening quote
                      ([^'"]+)            # capture variable name
                      ['"]                # closing quote
                   """
        matches = re.findall(pattern, content, re.VERBOSE)

        return sorted(set(matches))

    def __addEnvVar(self, name, value):
        if not name:
            return False

        file_path = os.path.join(Engine.project, ".htaccess")
        if not os.path.exists(file_path):
            return False

        content = cli.read(file_path)
        if content is None:
            return False

        if re.search(rf"^\s*SetEnv\s+{re.escape(name)}\b", content, re.MULTILINE):
            cli.trace(f"Variable '{name}' already exists. Skipping.")
            return True

        new_line = f'SetEnv {name} "{value}"'
        lines = content.splitlines()

        try:
            section_index = next(
                i
                for i, line in enumerate(lines)
                if line.strip() == "# Project Variables"
            )
        except StopIteration:
            updated_content = f"# Project Variables\n{new_line}\n\n{content}"
        else:
            insert_index = section_index + 1
            while insert_index < len(lines) and lines[insert_index].strip().startswith(
                "SetEnv"
            ):
                insert_index += 1
            lines.insert(insert_index, new_line)
            updated_content = "\n".join(lines) + "\n"

        if not cli.write(file_path, updated_content):
            return False

        cli.trace(f"Variable '{name}' added successfully.")

        return True

    def __getCodeBase(self, folder):
        if not folder:
            return ""

        extension_map = {
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".js": "js",
            ".php": "php",
            ".py": "python",
            ".json": "json",
            ".xml": "xml",
            ".txt": "text",
            ".md": "markdown",
            ".ts": "ts",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".go": "go",
            ".sh": "bash",
        }

        output = []
        files = sorted(
            f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))
        )

        for index, filename in enumerate(files, start=1):
            file_path = os.path.join(folder, filename)
            _, ext = os.path.splitext(filename)
            language = extension_map.get(ext.lower(), "")
            content = cli.read(file_path)
            block = f"{index}. {filename}\n" f"```{language}\n" f"{content}\n" f"```\n"
            output.append(block)

        return "\n".join(output)

    def __codeEditor(self, page_group="", page_name="", page_code={}):
        if not page_group:
            page_group = "group"
        if not page_group:
            page_group = "page"
        if len(page_code) == 0:
            return False

        config = json.loads(page_code.get("config.json", "{}"))
        group_path = os.path.join(Engine.project, page_group)
        page_path = os.path.join(Engine.project, page_group, page_name)
        page_exists = os.path.exists(os.path.join(page_path, "code.php"))

        Patch.add(group_path)
        os.makedirs(group_path, exist_ok=True)

        Patch.add(page_path)
        os.makedirs(page_path, exist_ok=True)

        for filename, content in page_code.items():
            if filename in [
                "config.json",
                # "",
            ]:
                continue
            file_path = os.path.join(page_path, filename)
            Patch.add(file_path)
            cli.write(file_path, content)

        if (
            not page_exists
            and "page.html" in page_code
            and page_code["page.html"].strip() != ""
        ):
            if not self.__groupMethodExists(page_group):
                group_prompt = self.__create_group__(
                    page_group,
                    config.get(
                        "group-description",
                        f"means that only {page_group} users can access the page",
                    ),
                )
                group_code = Engine.handler.__class__.code(group_prompt)
                if "function.php" in group_code:
                    self.__addGroupMethod(group_code["function.php"].strip())

        if "db.sql" in page_code and page_code["db.sql"].strip() != "":
            sql_file = os.path.join(page_path, "db.sql")
            if os.path.exists(sql_file):
                cli.command("code " + sql_file, False, True)
                if (
                    cli.selection("Confirm to update database", ["Go", "No"], True)
                    == "Go"
                ):
                    cli.trace("Updating database")
                    DB.submit(page_code["db.sql"])
            os.remove(sql_file)

        if "code.php" in page_code and page_code["code.php"].strip() != "":
            envars = self.__extractEnvVars(page_code["code.php"])
            if len(envars) > 0:
                for envar in envars:
                    self.__addEnvVar(envar, "")

        plugins = config.get("composer-plugins", [])
        if len(plugins) > 0:
            for plugin in plugins:
                if cli.selection(
                    f"Confirm to install Composer({plugin})", ["Go", "No"], True
                ):
                    Patch.add(os.path.join(Engine.project, "composer.json"))
                    Patch.add(os.path.join(Engine.project, "composer.lock"))
                    Patch.add(os.path.join(Engine.project, "vendor"))

                    cli.command(
                        "composer require " + plugin, True, False, Engine.project
                    )
                    print()

        return True

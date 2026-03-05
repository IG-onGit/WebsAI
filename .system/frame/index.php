<?php

class DB
{
    private static $charset = 'utf8mb4';
    private static $pdo = null;

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main
    /**
     * INSERT
     * Returns inserted ID or false
     */
    public static function insert($table = '', $data = [])
    {
        if (!$table || empty($data)) return false;

        try
        {
            $pdo = self::connect();
            $columns = array_keys($data);
            $fields = implode(',', $columns);
            $placeholders = ':' . implode(', :', $columns);
            $sql = "INSERT INTO {$table} ($fields) VALUES ($placeholders)";
            $stmt = $pdo->prepare($sql);

            foreach ($data as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            if ($stmt->execute()) return $pdo->lastInsertId();

            return false;
        }
        catch (Exception $e)
        {
            return false;
        }
    }

    /**
     * DELETE
     * Returns true or false
     */
    public static function delete($table = '', $where = [], $where_vars = [])
    {
        if (!$table || empty($where)) return false;

        try
        {
            $pdo = self::connect();
            $sql = "DELETE FROM {$table} WHERE " . self::buildSQL($where, ' and ');
            $stmt = $pdo->prepare($sql);

            foreach ($where_vars as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            return $stmt->execute();
        }
        catch (Exception $e)
        {

            return false;
        }
    }

    /**
     * UPDATE
     * Returns true or false
     */
    public static function update($table = '', $data = [], $where = [], $where_vars = [])
    {
        if (!$table || empty($data) || empty($where)) return false;

        try
        {
            $pdo = self::connect();
            $setParts = [];

            foreach ($data as $column => $value)
            {
                $setParts[] = "$column = :set_$column";
            }

            $setSQL = implode(', ', $setParts);
            $whereSQL = self::buildSQL($where, ' and ');
            $sql = "UPDATE {$table} SET $setSQL WHERE $whereSQL";
            $stmt = $pdo->prepare($sql);

            foreach ($data as $column => $value)
            {
                $stmt->bindValue(":set_$column", $value);
            }

            foreach ($where_vars as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            return $stmt->execute();
        }
        catch (Exception $e)
        {

            return false;
        }
    }

    /**
     * QUERY (SELECT)
     * Returns array of records
     */
    public static function query($statement = [], $statement_vars = [])
    {
        if (empty($statement)) return [];

        try
        {
            $pdo = self::connect();
            $sql = self::buildSQL($statement);
            $stmt = $pdo->prepare($sql);

            foreach ($statement_vars as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            $stmt->execute();

            return $stmt->fetchAll();
        }
        catch (Exception $e)
        {

            return [];
        }
    }

    /**
     * SUBMIT (Custom SQL)
     * Returns true or false
     */
    public static function submit($sql = [], $sql_vars = [])
    {
        if (empty($sql)) return false;

        try
        {
            $pdo = self::connect();
            $statement = self::buildSQL($sql);
            $stmt = $pdo->prepare($statement);

            foreach ($sql_vars as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            return $stmt->execute();
        }
        catch (Exception $e)
        {
            return false;
        }
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers
    /**
     * Create PDO connection (Singleton)
     */
    private static function connect()
    {
        if (self::$pdo === null)
        {
            $host = getenv('DB_HOST');
            $db   = getenv('DB_NAME');
            $user = getenv('DB_USER');
            $pass = getenv('DB_PASS');

            try
            {
                self::$pdo = new PDO("mysql:host=" . $host . ";dbname=" . $db . ";charset=" . self::$charset, $user, $pass, [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false,
                ]);
            }
            catch (PDOException $e)
            {
                die('Database connection failed: ' . $e->getMessage());
            }
        }

        return self::$pdo;
    }

    /**
     * Converts SQL line array to string
     */
    private static function buildSQL($lines = [], $delimiter = ' ')
    {
        if (!is_array($lines) || empty($lines))
        {
            return '';
        }

        return trim(implode($delimiter, $lines));
    }
}

class App
{
    private static $api = false;
    private static $group = '';
    private static $page = '';
    private static $action = '';
    private static $post = [];
    private static $get = [];
    private static $files = [];

    public function __construct()
    {
        $url = $this->url();
        $default = explode('/', getenv('WEBSAI_LANDING'));

        self::$page = isset($url['segments'][0]) ? $url['segments'][0] : '';
        self::$group = $this->detectGroup();

        if (empty(self::$group))
        {
            self::$group = $default[0];
            self::$page = $default[1];
        }

        $this->validateGroup();

        $request = $this->request();
        self::$post = $request['post'];
        self::$get = $request['get'];
        self::$files = $request['files'];
        self::$api = $this->detectAPI();
        self::$action = $this->detectAction();

        if (self::$api || !empty(self::$action)) return $this->executeAction();

        $html = $this->getContent("assets/page.html");
        $html .= $this->getContent(self::$group . '/' . self::$page . '/style.css');
        $html .= $this->getContent(self::$group . '/' . self::$page . '/page.html');
        $html .= $this->getContent(self::$group . '/' . self::$page . '/script.js');
        $html .= '<script>$(window).on("load", function() {App.loaded()});</script>';

        echo $html;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main
    /**
     * Send an error response
     * @param string $message - description of the error
     * @param mixed $response - optional data
     */
    public static function error($message, $response = null)
    {
        self::sendResponse(true, $message, $response);
    }

    /**
     * Send an informational response
     * @param string $message - information message
     * @param mixed $response - optional data
     */
    public static function info($message, $response = null)
    {
        self::sendResponse(false, $message, $response);
    }

    /**
     * Send a success response
     * @param string $message - success message
     * @param mixed $response - optional data
     */
    public static function success($message, $response = null)
    {
        self::sendResponse(false, $message, $response);
    }

    /**
     * Redirect to page
     * @param string $page - exiting group page e.g "public/landing"
     */
    public static function redirect($page)
    {
        if (empty($page)) return false;
        if (self::$api) exit;

        header("Location: /" . $page);
        exit;
    }

    /**
     * Get real path of page file or folder
     * @param string $path - page file path e.g "items/item.json"
     */
    public static function path($path)
    {
        return __DIR__ . '/' . $path;
    }

    /**
     * Get user's ID if authorized, or 0 if not;
     */
    public static function user()
    {
        self::ensureSession();

        if (!isset($_SESSION['websai_user_id'])) return 0;
        if (!is_numeric($_SESSION['websai_user_id'])) return 0;
        if ((int)$_SESSION['websai_user_id'] <= 0) return 0;

        return (int)$_SESSION['websai_user_id'];
    }

    /**
     * Register user in session
     */
    public static function login($user)
    {
        self::ensureSession();

        session_regenerate_id(true);
        $_SESSION['websai_session_time'] = time();
        $_SESSION['websai_user_id'] = (int)$user;

        return true;
    }

    /**
     * Remove user from session
     */
    public static function logout()
    {
        if (session_status() === PHP_SESSION_NONE) session_start();

        $_SESSION = [];
        session_destroy();

        return true;
    }

    /**
     * Gets environment variable value, or returns default
     */
    public static function env($name = '', $default = '')
    {
        if (!$name) return $default;
        if (isset($_SERVER[$name])) return $_SERVER[$name];

        $value = getenv($name);
        if ($value !== false) return $value;

        return $default;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers
    private static function sendResponse($error, $message, $response)
    {
        header('Content-Type: application/json');
        echo json_encode([
            'error' => $error,
            'message' => $message,
            'response' => $response
        ]);
        exit;
    }

    private function url()
    {
        $scheme = (
            (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ||
            ($_SERVER['SERVER_PORT'] ?? 80) == 443
        ) ? 'https' : 'http';

        $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
        $host = preg_replace('/[^a-zA-Z0-9\.\-:]/', '', $host);
        $uri = $_SERVER['REQUEST_URI'] ?? '/';
        $uri = filter_var($uri, FILTER_SANITIZE_URL);
        $url = $scheme . '://' . $host . $uri;
        $parts = parse_url($url);
        $segments = [];

        if (!empty($parts['path']))
        {
            $segments = array_values(
                array_filter(explode('/', trim($parts['path'], '/')))
            );
        }

        return [
            'url' => $url,
            'scheme' => $parts['scheme'] ?? '',
            'host' => $parts['host'] ?? '',
            'path' => $parts['path'] ?? '',
            'segments' => $segments
        ];
    }

    private function request()
    {
        static $data = null;
        if ($data !== null) return $data;

        $cleanArray = function (array $source): array
        {
            $clean = [];
            foreach ($source as $key => $value)
            {
                $safeKey = preg_replace('/[^a-zA-Z0-9_\-]/', '', $key);
                if ($safeKey === '') continue;

                if (is_array($value))
                {
                    $clean[$safeKey] = array_map(function ($v)
                    {
                        return $this->cleanRequestValue($v);
                    }, $value);
                }
                else
                {
                    $clean[$safeKey] = $this->cleanRequestValue($value);
                }
            }
            return $clean;
        };

        $cleanFiles = function (array $files): array
        {
            $clean = [];
            foreach ($files as $key => $file)
            {
                $safeKey = preg_replace('/[^a-zA-Z0-9_\-]/', '', $key);
                if ($safeKey === '') continue;

                if (is_array($file['name']))
                {
                    $clean[$safeKey] = [
                        'name' => array_map('cleanFileName', $file['name']),
                        'type' => $file['type'],
                        'tmp_name' => $file['tmp_name'],
                        'error' => $file['error'],
                        'size' => $file['size']
                    ];
                }
                else
                {
                    $clean[$safeKey] = [
                        'name' => $this->cleanFileName($file['name']),
                        'type' => $file['type'],
                        'tmp_name' => $file['tmp_name'],
                        'error' => $file['error'],
                        'size' => $file['size']
                    ];
                }
            }
            return $clean;
        };

        return [
            'get'   => $cleanArray($_GET),
            'post'  => $cleanArray($_POST),
            'files' => $cleanFiles($_FILES)
        ];
    }

    private function cleanRequestValue($value)
    {
        $value = str_replace("\0", '', $value);
        $value = trim($value);
        $value = strip_tags($value);
        $value = preg_replace('/[\x00-\x1F\x7F]/u', '', $value);

        return $value;
    }

    private function cleanFileName(string $name): string
    {
        $name = basename($name);
        $name = preg_replace('/[^a-zA-Z0-9_\.\-]/', '_', $name);

        return $name;
    }

    private function detectGroup()
    {
        if (empty(self::$page)) return '';

        $folder = __DIR__;
        $items = array_diff(scandir($folder), [
            '.',
            '..',
            '.git',
            '.env',
            '.vscode',
            'vendor',
            'assets',
            '.github',
            '.gitlab',
            '.gitignore',
            '.htaccess',
            'groups.php',
            'index.php',
            'LICENSE',
            'README.md',
            'robots.txt',
            'sitemap.xml',
            'composer.json',
            'composer.lock',
            // '',
        ]);

        $group = "";
        foreach ($items as $x)
        {
            $path = "{$folder}/{$x}/" . self::$page . '/code.php';
            if (!file_exists($path) || !is_readable($path)) continue;

            require_once $path;
            if (!class_exists(self::$page, false)) continue;

            $group = $x;
            break;
        }

        return $group;
    }

    private function getContent($file = '')
    {
        if (empty($file)) return '';

        $file = __DIR__ . '/' . $file;
        if (!is_file($file) || !file_exists($file) || !is_readable($file)) return '';

        $type = pathinfo($file, PATHINFO_EXTENSION);
        if ($type == 'html') return PHP_EOL . file_get_contents($file) . PHP_EOL;
        if ($type == 'css') return '<style>' . PHP_EOL . file_get_contents($file) . PHP_EOL . '</style>';
        if ($type == 'js') return '<script>' . PHP_EOL . file_get_contents($file) . PHP_EOL . '</script>';

        return file_get_contents($file);
    }

    private function detectAPI()
    {
        $file = __DIR__ . '/' . self::$group . '/' . self::$page . '/page.html';
        if (file_exists($file) && is_readable($file)) return false;

        return true;
    }

    private function detectAction()
    {
        if (!isset(self::$post['websai-call'])) return '';
        if (empty(self::$post['websai-call'])) return '';
        if (!method_exists(ucfirst(self::$page), self::$post['websai-call'])) return '';

        return self::$post['websai-call'];
    }

    private function executeAction()
    {
        if (empty(self::$page) || empty(self::$action)) die;

        $class = ucfirst(self::$page);
        $method = self::$action;
        $object = new $class();
        $object->$method(self::$post, self::$get, self::$files);

        die;
    }

    private static function ensureSession()
    {
        if (session_status() === PHP_SESSION_NONE) session_start();

        if (!isset($_SESSION['websai_session_time']))
        {
            $_SESSION['websai_session_time'] = time();
        }

        if (time() - $_SESSION['websai_session_time'] >= 1800) // 30 minutes
        {
            session_regenerate_id(true);
            $_SESSION['websai_session_time'] = time();
        }
    }

    private function validateGroup()
    {
        $group = self::$group;
        if (empty($group)) return '';

        require_once 'groups.php';
        if (!class_exists('Groups', false)) return '';
        if (!method_exists('Groups', $group)) return $group;
        if (!Groups::$group(self::$post, self::$get, self::$files)) return '';

        return self::$group;
    }
}

$app = new App();

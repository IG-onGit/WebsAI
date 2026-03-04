from imports import *


class DB:
    ####################################################################################// Params
    _engine = None
    _Session = None
    _session = None
    _host = ""
    _user = ""
    _pass = ""

    ####################################################################################// Load
    def __init__(self, host, database, user, password, driver="pymysql"):
        conn_str = f"mysql+{driver}://{user}:{password}@{host}/{database}"
        DB._engine = create_engine(conn_str, echo=False, future=True)
        DB._Session = sessionmaker(bind=DB._engine, future=True)
        DB._session = DB._Session()
        DB._host = host
        DB._user = user
        DB._pass = password
        pass

    ####################################################################################// Main
    def new(name):
        engine = create_engine(f"mysql+pymysql://{DB._user}:{DB._pass}@{DB._host}/")
        with engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
                )
            )
            conn.commit()
        engine.dispose()
        pass

    def insert(table, data):
        try:
            cols = ", ".join(data.keys())
            vals = ", ".join([f":{k}" for k in data.keys()])
            sql = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
            with DB._engine.begin() as conn:
                result = conn.execute(text(sql), data)
                return result.lastrowid if result.lastrowid else False
        except Exception as e:
            cli.error(f"Insert error: {e}")
            return False
        return False

    def update(table, data, where, params=None):
        try:
            set_clause = ", ".join([f"{k}=:{k}" for k in data.keys()])
            combined_params = {**data, **(params or {})}
            sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
            with DB._engine.begin() as conn:
                conn.execute(text(sql), combined_params)
            return True
        except Exception as e:
            cli.error(f"Update error: {e}")
            return False
        return False

    def delete(table, where, params=None):
        try:
            sql = f"DELETE FROM {table} WHERE {where}"
            with DB._engine.begin() as conn:
                conn.execute(text(sql), params or {})
            return True
        except Exception as e:
            cli.error(f"Delete error: {e}")
            return False
        return False

    def query(statement, params=None):
        try:
            with DB._engine.connect() as conn:
                result = conn.execute(text(statement), params or {})
                return [dict(row) for row in result.mappings().all()]
        except Exception as e:
            cli.error(f"Query error: {e}")
            return []

    def submit(sql, params=None):
        try:
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            with DB._engine.begin() as conn:
                for stmt in statements:
                    conn.execute(text(stmt), params or {})
            return True
        except Exception as e:
            cli.error(f"Submit error: {e}")
            return False
        return False

    def schema():
        try:
            with DB._engine.connect() as conn:
                tables = conn.execute(text("SHOW TABLES")).fetchall()
                ddl = []

                for (table,) in tables:
                    result = conn.execute(text(f"SHOW CREATE TABLE {table}"))
                    row = result.fetchone()
                    ddl.append(row[1] + ";\n")

                return "\n".join(ddl)

        except Exception as e:
            cli.error(f"Schema error: {e}")
            return ""
        return ""

    def close():
        if DB._engine == None:
            return False

        cli.trace("Closing database connection")
        DB._session.close()
        DB._engine.dispose()
        DB._engine = None
        DB._Session = None
        DB._session = None

        return True

    ####################################################################################// Helpers

import psycopg2

from logrec.local_properties import DB_DBNAME, DB_USER, DB_HOST, DB_PASSWORD


class DAO(object):
    TABLE = 'LANGSTATS'
    PROJECTS_TABLE = 'PROJECTS'

    def __init__(self):
        conn = psycopg2.connect(f"dbname='{DB_DBNAME}' user='{DB_USER}' host='{DB_HOST}' password='{DB_PASSWORD}'")
        conn.set_session(autocommit=True)
        self.cur = conn.cursor()
        self.processed_projects_cache = self.__get_processed_projects()
        self.created_projects = self.__get_created_projects()

    def save_row(self, row):
        project = row[0]
        if project not in self.created_projects:
            self.cur.execute(f"INSERT INTO {DAO.PROJECTS_TABLE} (PROJECT, PROCESSED) VALUES (%s, FALSE)", (project,))
            self.created_projects.append(project)
        self.cur.execute(f'INSERT INTO {DAO.TABLE} (PROJECT, FILE, ' \
                         ' CODE_TOTAL, CODE_TOTAL_UQ, CODE_NON_ENG, CODE_NON_ENG_UQ, CODE_PERCENT, CODE_PERCENT_UQ,' \
                         ' CODE_STR_TOTAL, CODE_STR_TOTAL_UQ, CODE_STR_NON_ENG, CODE_STR_NON_ENG_UQ, CODE_STR_PERCENT, CODE_STR_PERCENT_UQ,' \
                         ' CODE_STR_COM_TOTAL, CODE_STR_COM_TOTAL_UQ, CODE_STR_COM_NON_ENG, CODE_STR_COM_NON_ENG_UQ, CODE_STR_COM_PERCENT, CODE_STR_COM_PERCENT_UQ, SAMPLE) ' \
                         'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                         row)

    def purge(self):
        self.cur.execute(f"DELETE FROM {DAO.PROJECTS_TABLE}")

    def save_processed_project(self, project):
        self.cur.execute(f"UPDATE {DAO.PROJECTS_TABLE} SET PROCESSED=TRUE where PROJECT=%s", (project,))
        self.processed_projects_cache.append(project)

    def select_noneng_projects(self, code_percent, code_noneng, code_noneng_uq, code_str_percent, code_str_noneng,
                               code_str_noneng_uq):
        self.cur.execute(
            f"select concat('test/', project,'/', file) as fullpath from {DAO.TABLE} where ((code_percent > {code_percent} and code_non_eng > {code_noneng} and code_non_eng_uq > {code_noneng_uq}) or (code_str_percent > {code_str_percent} and code_str_non_eng > {code_str_noneng} and code_str_non_eng_uq > {code_str_noneng_uq}))")
        return list(map(lambda x: x[0], self.cur.fetchall()))

    def __get_processed_projects(self):
        self.cur.execute(f"SELECT PROJECT from {DAO.PROJECTS_TABLE} where PROCESSED = TRUE")
        return list(map(lambda x: x[0], self.cur.fetchall()))

    def __get_created_projects(self):
        self.cur.execute(f"SELECT PROJECT from {DAO.PROJECTS_TABLE}")
        return list(map(lambda x: x[0], self.cur.fetchall()))

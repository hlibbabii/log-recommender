import psycopg2

from local_properties import DB_DBNAME, DB_USER, DB_HOST, DB_PASSWORD


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

    def __get_processed_projects(self):
        self.cur.execute(f"SELECT PROJECT from {DAO.PROJECTS_TABLE} where PROCESSED = TRUE")
        return list(map(lambda x: x[0], self.cur.fetchall()))

    def __get_created_projects(self):
        self.cur.execute(f"SELECT PROJECT from {DAO.PROJECTS_TABLE}")
        return list(map(lambda x: x[0], self.cur.fetchall()))

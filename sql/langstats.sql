CREATE TABLE PROJECTS (
  PROJECT TEXT NOT NULL,
  PROCESSED BOOLEAN NOT NULL,
  PRIMARY KEY(PROJECT)
);

CREATE TABLE LANGSTATS(
   PROJECT                        TEXT    NOT NULL,
   FILE                           TEXT    NOT NULL,

   CODE_TOTAL                     INT     NOT NULL,
   CODE_TOTAL_UQ                  INT     NOT NULL,
   CODE_NON_ENG                   INT     NOT NULL,
   CODE_NON_ENG_UQ                INT     NOT NULL,
   CODE_PERCENT                   REAL    NOT NULL,
   CODE_PERCENT_UQ                REAL    NOT NULL,

   CODE_STR_TOTAL                 INT     NOT NULL,
   CODE_STR_TOTAL_UQ              INT     NOT NULL,
   CODE_STR_NON_ENG               INT     NOT NULL,
   CODE_STR_NON_ENG_UQ            INT     NOT NULL,
   CODE_STR_PERCENT               REAL    NOT NULL,
   CODE_STR_PERCENT_UQ            REAL    NOT NULL,

   CODE_STR_COM_TOTAL             INT     NOT NULL,
   CODE_STR_COM_TOTAL_UQ          INT     NOT NULL,
   CODE_STR_COM_NON_ENG           INT     NOT NULL,
   CODE_STR_COM_NON_ENG_UQ        INT     NOT NULL,
   CODE_STR_COM_PERCENT           REAL    NOT NULL,
   CODE_STR_COM_PERCENT_UQ        REAL    NOT NULL,
   SAMPLE                         TEXT,
   PRIMARY KEY(PROJECT, FILE),
   FOREIGN KEY(PROJECT) REFERENCES PROJECTS(PROJECT) ON DELETE CASCADE
);

CREATE TABLE NONENG_MANUAL_TAGS(
   PROJECT                        TEXT       NOT NULL,
   FILE                           TEXT       NOT NULL,

   NONENG                         BOOLEAN    NOT NULL,
   PRIMARY KEY(PROJECT, FILE)
);

select concat('/home/lv71161/hlibbabii/raw_datasets/devanbu/data/multilang_100_percent/test/', project,'/', file) as fullpath, code_percent, code_str_percent, code_str_com_percent, sample from langstats where ((code_percent > 0.005 and code_non_eng_uq > 2) or (code_str_percent > 0.005 and code_str_non_eng_uq > 2)) and char_length(file)%15=0

select l.project, l.file, l.code_percent, l.code_str_percent, t.noneng from noneng_manual_tags as t inner join langstats as l on t.file = l.file and l.project = l.project order by l.code_percent
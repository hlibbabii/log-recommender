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
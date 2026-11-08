-- SADA: subconjunto do esquema do web acadêmico (PostgreSQL 16).
-- Nomes de tabelas e colunas seguem o banco da instituição; as restrições CHECK foram
-- acrescentadas para que a base simulada rejeite dados incoerentes com as regras.

CREATE TABLE inativo (
    codigoinativo  SMALLINT    PRIMARY KEY,
    descricao      VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE curso (
    codigocurso  SMALLINT     PRIMARY KEY CHECK (codigocurso BETWEEN 0 AND 99),
    nomecurso    VARCHAR(120) NOT NULL,
    sigla        VARCHAR(10)  NOT NULL UNIQUE
);

CREATE TABLE gradecurricular (
    codigograde     SMALLINT     PRIMARY KEY,
    codigocurso     SMALLINT     NOT NULL REFERENCES curso (codigocurso),
    nomegrade       VARCHAR(80)  NOT NULL,
    anoinicio       SMALLINT     NOT NULL,
    semestreinicio  SMALLINT     NOT NULL CHECK (semestreinicio IN (1, 2))
);

CREATE TABLE disciplina (
    codigodisciplina  INTEGER      PRIMARY KEY,
    nomedisciplina    VARCHAR(120) NOT NULL,
    cargahoraria      SMALLINT     NOT NULL CHECK (cargahoraria > 0),
    credito           SMALLINT     NOT NULL CHECK (credito >= 0),
    estagio           BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE gradedisciplina (
    codigograde       SMALLINT NOT NULL REFERENCES gradecurricular (codigograde),
    codigodisciplina  INTEGER  NOT NULL REFERENCES disciplina (codigodisciplina),
    periodo           SMALLINT NOT NULL CHECK (periodo BETWEEN 1 AND 12),
    PRIMARY KEY (codigograde, codigodisciplina)
);

CREATE TABLE professor (
    codigoprofessor    INTEGER      PRIMARY KEY,
    nomeprofessor      VARCHAR(120) NOT NULL,
    cpf                VARCHAR(11),
    formacaoprofessor  VARCHAR(30)
);

CREATE TABLE periodoletivo (
    codigoperiodoletivo  INTEGER  PRIMARY KEY,
    ano                  SMALLINT NOT NULL,
    semestre             SMALLINT NOT NULL CHECK (semestre IN (1, 2)),
    datainicio           DATE     NOT NULL,
    datafim              DATE     NOT NULL,
    CHECK (datafim > datainicio),
    UNIQUE (ano, semestre)
);

CREATE TABLE aluno (
    codigoaluno       INTEGER      PRIMARY KEY,
    matricula         VARCHAR(10)  NOT NULL UNIQUE,
    anoingresso       SMALLINT     NOT NULL,
    semestreingresso  SMALLINT     NOT NULL CHECK (semestreingresso IN (1, 2)),
    codigoturno       SMALLINT     NOT NULL,
    codigocurso       SMALLINT     NOT NULL REFERENCES curso (codigocurso),
    nomealuno         VARCHAR(120) NOT NULL,
    cpf               VARCHAR(11),
    codigograde       SMALLINT     NOT NULL REFERENCES gradecurricular (codigograde),
    periodoatual      SMALLINT     CHECK (periodoatual BETWEEN 1 AND 12),
    concluinte        BOOLEAN      NOT NULL DEFAULT FALSE,
    codigoinativo     SMALLINT     REFERENCES inativo (codigoinativo),
    -- RN06: dez dígitos; o quinto (semestre) é 1 ou 2
    CONSTRAINT ck_matricula_formato CHECK (matricula ~ '^[0-9]{4}[12][0-9]{5}$'),
    -- RN06: AA CC S T coerentes com os atributos do cadastro (CASE evita o cast inválido)
    CONSTRAINT ck_matricula_coerencia CHECK (
        CASE WHEN matricula ~ '^[0-9]{10}$' THEN
            substr(matricula, 1, 2)::INT = anoingresso % 100
            AND substr(matricula, 3, 2)::INT = codigocurso
            AND substr(matricula, 5, 1)::INT = semestreingresso
            AND substr(matricula, 6, 1)::INT = codigoturno
        ELSE TRUE END)
);

CREATE TABLE turma (
    codigoturma          INTEGER  PRIMARY KEY,
    codigodisciplina     INTEGER  NOT NULL REFERENCES disciplina (codigodisciplina),
    codigoprofessor      INTEGER  NOT NULL REFERENCES professor (codigoprofessor),
    codigoperiodoletivo  INTEGER  NOT NULL REFERENCES periodoletivo (codigoperiodoletivo),
    sequenciaturma       SMALLINT NOT NULL CHECK (sequenciaturma > 0),
    capacidade           SMALLINT NOT NULL CHECK (capacidade > 0),
    diasletivos          SMALLINT NOT NULL CHECK (diasletivos >= 0),
    diarioencerrado      BOOLEAN  NOT NULL DEFAULT FALSE,
    UNIQUE (codigodisciplina, codigoperiodoletivo, sequenciaturma)
);

CREATE TABLE diario (
    codigodiario  INTEGER      PRIMARY KEY,
    codigoaluno   INTEGER      NOT NULL REFERENCES aluno (codigoaluno),
    codigoturma   INTEGER      NOT NULL REFERENCES turma (codigoturma),
    nota1         NUMERIC(4,2) CHECK (nota1 BETWEEN 0 AND 10),
    nota2         NUMERIC(4,2) CHECK (nota2 BETWEEN 0 AND 10),
    nota          NUMERIC(4,2) CHECK (nota BETWEEN 0 AND 10),
    notafinal     NUMERIC(4,2) CHECK (notafinal BETWEEN 0 AND 10),
    faltas        SMALLINT     NOT NULL DEFAULT 0 CHECK (faltas >= 0),
    resultado     VARCHAR(16)
        CHECK (resultado IN ('APROVADO', 'REPROVADO_NOTA', 'REPROVADO_FALTA')),
    UNIQUE (codigoaluno, codigoturma)
);

-- Tabela própria do SADA: vincula o usuário do Django ao professor do web acadêmico (RN07).
CREATE TABLE sada_perfil_professor (
    usuario_id       BIGINT  PRIMARY KEY REFERENCES auth_user (id),
    codigoprofessor  INTEGER NOT NULL UNIQUE REFERENCES professor (codigoprofessor)
);

CREATE INDEX ix_diario_turma   ON diario (codigoturma);
CREATE INDEX ix_diario_aluno   ON diario (codigoaluno);
CREATE INDEX ix_turma_periodo  ON turma (codigoperiodoletivo);
CREATE INDEX ix_turma_disc     ON turma (codigodisciplina);
CREATE INDEX ix_aluno_coorte   ON aluno (anoingresso, semestreingresso);

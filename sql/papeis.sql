-- SADA: papel de leitura com privilégio mínimo (LGPD, art. 6º, III: necessidade).
-- O SADA lê o banco do web acadêmico sem poder alterá-lo e sem enxergar as colunas
-- de identificação direta que a análise não utiliza (CPF).
CREATE ROLE sada_leitura NOLOGIN;

GRANT SELECT ON curso, gradecurricular, disciplina, gradedisciplina, periodoletivo,
                turma, diario, inativo TO sada_leitura;
-- nome e matrícula são necessários para a lista de risco; o CPF permanece inacessível
GRANT SELECT (codigoaluno, matricula, anoingresso, semestreingresso, codigoturno, codigocurso,
              nomealuno, codigograde, periodoatual, concluinte, codigoinativo)
    ON aluno TO sada_leitura;
GRANT SELECT (codigoprofessor, nomeprofessor, formacaoprofessor)
    ON professor TO sada_leitura;

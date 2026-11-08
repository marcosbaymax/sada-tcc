-- Q1: taxa de aprovação por disciplina (diários encerrados)
SELECT gd.periodo AS periodo_curricular, d.nomedisciplina,
       COUNT(*) AS registros,
       ROUND(100.0 * COUNT(*) FILTER (WHERE di.resultado = 'APROVADO') / COUNT(*), 1) AS taxa_aprovacao,
       ROUND(AVG(di.nota), 2) AS media
FROM diario di
JOIN turma t            ON t.codigoturma = di.codigoturma
JOIN disciplina d       ON d.codigodisciplina = t.codigodisciplina
JOIN aluno a            ON a.codigoaluno = di.codigoaluno
JOIN gradedisciplina gd ON gd.codigograde = a.codigograde
                       AND gd.codigodisciplina = d.codigodisciplina
WHERE t.diarioencerrado
GROUP BY gd.periodo, d.codigodisciplina, d.nomedisciplina
ORDER BY taxa_aprovacao, d.codigodisciplina;

-- Q2: evolução por período letivo
SELECT p.ano || '.' || p.semestre AS periodo,
       COUNT(*) AS registros,
       ROUND(100.0 * COUNT(*) FILTER (WHERE di.resultado = 'APROVADO') / COUNT(*), 1) AS taxa_aprovacao,
       ROUND(AVG(di.nota), 2) AS media,
       ROUND(AVG(100.0 * (t.diasletivos * 2 - di.faltas) / (t.diasletivos * 2)), 1) AS frequencia
FROM diario di
JOIN turma t           ON t.codigoturma = di.codigoturma
JOIN periodoletivo p   ON p.codigoperiodoletivo = t.codigoperiodoletivo
WHERE t.diarioencerrado
GROUP BY p.ano, p.semestre
ORDER BY p.ano, p.semestre;

-- Q3: estudantes em risco no período em curso (RN09): frequência < 75 %
--     ou média parcial < 7,0 (atenção: 4,0 a 6,99, crítico: abaixo de 4,0)
SELECT DISTINCT a.matricula, a.nomealuno
FROM diario di
JOIN aluno a           ON a.codigoaluno = di.codigoaluno
JOIN turma t           ON t.codigoturma = di.codigoturma
JOIN periodoletivo p   ON p.codigoperiodoletivo = t.codigoperiodoletivo
WHERE NOT t.diarioencerrado
  AND p.ano = 2026 AND p.semestre = 2
  AND ( 100.0 * (t.diasletivos * 2 - di.faltas) / (t.diasletivos * 2) < 75.0
        OR COALESCE((COALESCE(di.nota1, 0) + COALESCE(di.nota2, 0))
                    / NULLIF((di.nota1 IS NOT NULL)::INT + (di.nota2 IS NOT NULL)::INT, 0),
                    10) < 7.0 )
ORDER BY a.matricula;

-- Q4: coeficiente de rendimento (RN05): média das notas finais ponderada pela carga
--     horária, com as disciplinas cursadas e sem os estágios
SELECT a.matricula,
       ROUND(SUM(COALESCE(di.notafinal, di.nota) * d.cargahoraria) / SUM(d.cargahoraria), 2) AS cr
FROM diario di
JOIN aluno a      ON a.codigoaluno = di.codigoaluno
JOIN turma t      ON t.codigoturma = di.codigoturma
JOIN disciplina d ON d.codigodisciplina = t.codigodisciplina
WHERE t.diarioencerrado AND NOT d.estagio
GROUP BY a.matricula
ORDER BY cr DESC, a.matricula;

-- Q5: situação atual por coorte de ingresso (ano e semestre da matrícula)
SELECT a.anoingresso || '.' || a.semestreingresso AS coorte,
       COUNT(*) AS ingressantes,
       COUNT(*) FILTER (WHERE a.concluinte) AS concluintes,
       COUNT(*) FILTER (WHERE a.codigoinativo = 2 AND NOT a.concluinte) AS evadidos,
       ROUND(100.0 * COUNT(*) FILTER (WHERE a.codigoinativo = 2 AND NOT a.concluinte)
             / COUNT(*), 1) AS taxa_evasao
FROM aluno a
GROUP BY a.anoingresso, a.semestreingresso
ORDER BY a.anoingresso, a.semestreingresso;

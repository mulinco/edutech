--1. Listar todos os cursos com nome da categoria e do instrutor
SELECT
    c.titulo AS "Título do Curso",
    cat.nome AS "Categoria",
    i.nome AS "Nome do Instrutor"
FROM
    curso c
JOIN
    categoria cat ON c.categoria_id = cat.id
JOIN
    instrutor i ON c.instrutor_id = i.id
ORDER BY
    c.titulo;

--2. Listar todos os alunos matriculados em um curso específico
SELECT
    a.nome AS "Nome do Aluno",
    a.email AS "Email",
    m.data_matricula AS "Data da Matrícula"
FROM
    aluno a
JOIN
    matricula m ON a.id = m.aluno_id
WHERE
    m.curso_id = 1;

--3. Exibir todas as aulas de um curso ordenadas por módulo e ordem
SELECT
    m.titulo AS "Módulo",
    a.titulo AS "Aula",
    a.ordem AS "Ordem da Aula"
FROM
    aula a
JOIN
    modulo m ON a.modulo_id = m.id
WHERE
    m.curso_id = 1 
ORDER BY
    m.ordem, a.ordem;

-- 4. Calcular a média de avaliações de cada curso 
SELECT
    c.titulo AS "Curso",
    -- COALESCE mostra 0.00 se o curso não tiver avaliações
    ROUND(COALESCE(AVG(av.nota), 0.0), 2) AS "Média de Avaliações"
FROM
    curso c
LEFT JOIN -- LEFT JOIN para incluir cursos que ainda não têm avaliações
    avaliacoes av ON c.id = av.curso_id
GROUP BY
    c.id, c.titulo
ORDER BY
    "Média de Avaliações" DESC;

--5. Contar quantos alunos estão matriculados por curso 
SELECT
    c.titulo AS "Curso",
    COUNT(m.aluno_id) AS "Total de Alunos"
FROM
    curso c
LEFT JOIN -- LEFT JOIN para incluir cursos com 0 alunos
    matricula m ON c.id = m.curso_id
GROUP BY
    c.id, c.titulo
ORDER BY
    "Total de Alunos" DESC;

--6. Calcular o faturamento total por categoria 
SELECT
    cat.nome AS "Categoria",
    -- COALESCE mostra 0.00 para categorias sem faturamento
    COALESCE(SUM(p.valor), 0.00) AS "Faturamento Total"
FROM
    categoria cat
LEFT JOIN
    curso c ON cat.id = c.categoria_id
LEFT JOIN
    matricula m ON c.id = m.curso_id
LEFT JOIN
    pagamento p ON m.id = p.matricula_id
WHERE
    p.status_pagamento = 'Aprovado'
GROUP BY
    cat.id, cat.nome
ORDER BY
    "Faturamento Total" DESC;

--7. Identificar o curso com maior número de matrículas ativas
SELECT
    c.titulo AS "Curso",
    COUNT(m.id) AS "Matrículas Ativas"
FROM
    curso c
JOIN
    matricula m ON c.id = m.curso_id
WHERE
    m.status = 'ativa' -- Filtra apenas matrículas com o status 'ativa'
GROUP BY
    c.id, c.titulo
ORDER BY
    "Matrículas Ativas" DESC
LIMIT 1; 


--8. Listar alunos, cursos matriculados e porcentagem de conclusão Esta é a consulta mais complexa, que usa CTEs (WITH) para quebrar o problema.
WITH AulasPorCurso AS (
    -- 1. Conta o total de aulas de cada curso
    SELECT
        m.curso_id,
        COUNT(a.id) AS total_aulas
    FROM aula a
    JOIN modulo m ON a.modulo_id = m.id
    GROUP BY m.curso_id
),
AulasConcluidas AS (
    -- 2. Conta quantas aulas foram concluídas por matrícula
    SELECT
        matricula_id,
        COUNT(aula_id) AS aulas_concluidas
    FROM progresso_aula
    WHERE concluida = TRUE
    GROUP BY matricula_id
)
-- 3. Junta tudo para o relatório final
SELECT
    a.nome AS "Aluno",
    c.titulo AS "Curso",
    COALESCE(ac.aulas_concluidas, 0) AS "Aulas Concluídas",
    COALESCE(apc.total_aulas, 0) AS "Total de Aulas no Curso",
    -- Usamos 100.0 para forçar a divisão com casas decimais
    CASE
        WHEN COALESCE(apc.total_aulas, 0) > 0
        THEN ROUND((COALESCE(ac.aulas_concluidas, 0) * 100.0) / apc.total_aulas, 2)
        ELSE 0.0
    END || '%' AS "Progresso"
FROM
    matricula m
JOIN
    aluno a ON m.aluno_id = a.id
JOIN
    curso c ON m.curso_id = c.id
LEFT JOIN
    AulasPorCurso apc ON c.id = apc.curso_id
LEFT JOIN
    AulasConcluidas ac ON m.id = ac.matricula_id
ORDER BY
    a.nome, c.titulo;


--9. Relatório completo de um curso: instrutor, número de alunos, média de avaliações, faturamento
SELECT
    c.titulo AS "Curso",
    i.nome AS "Instrutor",
    
    (SELECT COUNT(*) FROM matricula m WHERE m.curso_id = c.id) AS "Número de Alunos",
    
    (SELECT ROUND(COALESCE(AVG(nota), 0.0), 2) FROM avaliacoes av WHERE av.curso_id = c.id) AS "Média de Avaliações",
    
    (SELECT COALESCE(SUM(p.valor), 0.00)
     FROM pagamento p
     JOIN matricula m ON p.matricula_id = m.id
     WHERE m.curso_id = c.id AND p.status_pagamento = 'Aprovado') AS "Faturamento Total"
FROM
    curso c
JOIN
    instrutor i ON c.instrutor_id = i.id
WHERE
    c.id = 1;

--10. Listar instrutores com quantidade de cursos, total de alunos e média geral de avaliações
SELECT
    i.nome AS "Instrutor",
    COUNT(DISTINCT c.id) AS "Total de Cursos",
    COUNT(DISTINCT m.aluno_id) AS "Total de Alunos Únicos",
    ROUND(COALESCE(AVG(av.nota), 0.0), 2) AS "Média Geral de Avaliações"
FROM
    instrutor i
LEFT JOIN
    curso c ON i.id = c.instrutor_id
LEFT JOIN
    matricula m ON c.id = m.curso_id
LEFT JOIN
    avaliacoes av ON c.id = av.curso_id
GROUP BY
    i.id, i.nome
ORDER BY
    "Média Geral de Avaliações" DESC, "Total de Alunos Únicos" DESC;


--11. Top 5 cursos mais rentáveis (considerar pagamentos aprovados)
SELECT
    c.titulo AS "Curso",
    SUM(p.valor) AS "Receita Total"
FROM
    curso c
JOIN
    matricula m ON c.id = m.curso_id
JOIN
    pagamento p ON m.id = p.matricula_id
WHERE
    p.status_pagamento = 'Aprovado'
GROUP BY
    c.id, c.titulo
ORDER BY
    "Receita Total" DESC
LIMIT 5;

--12. Alunos que não concluíram nenhum curso nos últimos 6 meses
SELECT
    a.nome AS "Aluno",
    a.email AS "Email"
FROM
    aluno a
WHERE
    a.id NOT IN (
        -- Esta subquery encontra todos os alunos que CONCLUÍRAM um curso nos últimos 6 meses.
        SELECT DISTINCT aluno_id
        FROM matricula
        WHERE status = 'concluida'
          AND data_conclusao >= (CURRENT_DATE - INTERVAL '6 months')
    )
ORDER BY
    a.nome;
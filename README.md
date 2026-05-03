# Timesheet Analyzer

Solução para o desafio de seleção Dev Jr. da UnMEP.

Aplicação containerizada que lê um dataset de registros de timesheet, aplica
regras de negócio, agrega os dados e persiste um resumo analítico em JSON —
tudo isso executado com um único comando Docker.

---

## Sumário

- [Visão geral](#visão-geral)
- [Fluxo de processamento](#fluxo-de-processamento)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Regras de negócio](#regras-de-negócio)
- [Saída gerada](#saída-gerada)
- [Como executar](#como-executar)
- [Decisões técnicas](#decisões-técnicas)

---

## Visão geral

A aplicação recebe um arquivo `data.json` com 300 registros de horas
trabalhadas por funcionários em tarefas de desenvolvimento. A partir disso,
ela calcula totais, percentuais, rankings e identifica padrões — gerando um
`result.json` determinístico e equivalente ao gabarito fornecido.

Linguagem: **Python 3.12**  
Dependências externas: **nenhuma** (stdlib pura)  
Imagem base: **python:3.12-alpine**

---

## Fluxo de processamento

---

## Estrutura do projeto

```
.
├── main.py              # toda a lógica de processamento
├── data.json            # dataset de entrada (300 registros)
├── Dockerfile           # imagem python:3.12-alpine
├── docker-compose.yml   # orquestração e mapeamento de volume
└── README.md
```

---

## Regras de negócio

### 2.1 Tratamento de dados

Registros com `minutes <= 0` são descartados antes de qualquer agregação.
A quantidade de registros descartados é reportada no campo `ignoredRecords`.

### 2.2 Total por tarefa

Os registros válidos são agrupados por `taskId`. Os minutos de cada entrada
são somados, produzindo o total acumulado por tarefa.

### 2.3 Tarefa mais trabalhada

A tarefa com o maior `totalMinutes` após a agregação é identificada e
retornada com todos os seus campos no campo `mostWorkedTask`.

### 2.4 Percentual por tarefa

Cada tarefa recebe um percentual calculado sobre o total geral de minutos:

```
percentage = (taskMinutes / totalMinutes) * 100
```

Formatado com duas casas decimais seguidas de `%` (ex: `14.25%`).

### 2.5 Top 3 tarefas

As três tarefas com maior `totalMinutes` são retornadas em `top3TasksPercentage`,
contendo `taskId`, `taskName` e `percentage`.

### 2.6 Top 3 funcionários

Os três usuários com maior soma de minutos são retornados em `top3Employees`,
contendo `userId`, `userName` e `totalMinutes`.

### 2.7 Usuário com mais tarefas distintas

Identifica o usuário que apareceu em mais `taskId` diferentes ao longo de
todos os registros válidos. Retorna `userId`, `userName`, `distinctTasks`
(contagem) e `taskIds` (lista ordenada dos IDs).

### Regras de ordenação (desempate)

| Conjunto       | Critério 1          | Critério 2 (empate) |
|----------------|---------------------|----------------------|
| Tasks          | `totalMinutes` desc | `taskId` asc         |
| Funcionários   | `totalMinutes` desc | `userId` asc         |
| Distinct user  | `distinctTasks` desc| `userId` asc         |

---

## Saída gerada

O arquivo `result.json` segue exatamente a estrutura abaixo:

```json
{
  "totalMinutes": 28408,
  "tasks": [
    {
      "taskId": 103,
      "taskName": "Ajustar layout",
      "totalMinutes": 4047,
      "percentage": "14.25%"
    }
  ],
  "mostWorkedTask": {
    "taskId": 103,
    "taskName": "Ajustar layout",
    "totalMinutes": 4047,
    "percentage": "14.25%"
  },
  "top3TasksPercentage": [
    { "taskId": 103, "taskName": "Ajustar layout",           "percentage": "14.25%" },
    { "taskId": 110, "taskName": "Criar endpoint relatório", "percentage": "12.32%" },
    { "taskId": 106, "taskName": "Criar testes unitários",   "percentage": "10.74%" }
  ],
  "top3Employees": [
    { "userId": 5, "userName": "Eduardo", "totalMinutes": 4303 },
    { "userId": 1, "userName": "Ana",     "totalMinutes": 4077 },
    { "userId": 3, "userName": "Carla",   "totalMinutes": 3842 }
  ],
  "mostDistinctUserOnTasks": {
    "userId": 1,
    "userName": "Ana",
    "distinctTasks": 10,
    "taskIds": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
  },
  "ignoredRecords": 41
}
```

---

## Como executar

**Pré-requisito:** Docker Desktop instalado e em execução.

```bash
docker compose up --build
```

Ao final da execução, o `result.json` estará disponível:

- dentro do container em `/app/result.json`
- no diretório do projeto no host (mapeado via volume)

Saída esperada no terminal:

```
[INFO] Reading /app/data.json ...
[INFO] 300 total records loaded
[INFO] Valid: 259 | Ignored: 41
[INFO] Total minutes: 28408
[INFO] Most worked task: Ajustar layout (4047 min)
[INFO] Top employee: Eduardo (4303 min)
[OK]  result.json saved → /app/result.json
[OK]  result.json copiado para o diretório do host
```

---

## Decisões técnicas

**Python puro, sem dependências externas**  
Toda a lógica usa apenas `json`, `collections.defaultdict` e `pathlib`.
Isso elimina camadas de instalação, reduz o tamanho da imagem e garante
que a aplicação rode em qualquer ambiente com Python 3.12.

**Imagem python:3.12-alpine**  
Alpine Linux resulta em uma imagem final de aproximadamente 50MB, contra
os ~900MB de uma imagem Debian padrão. Para uma aplicação de processamento
de dados sem dependências nativas, é a escolha mais eficiente.

**Lógica genérica, sem hardcode**  
Nenhum valor do gabarito está fixado no código. Todos os resultados são
derivados exclusivamente do `data.json` lido em tempo de execução. A
aplicação produziria resultados corretos para qualquer dataset com a mesma
estrutura.

**Determinismo**  
A ordenação dupla (valor principal + id como desempate) garante que a saída
seja idêntica em qualquer execução, independente da ordem dos registros no
arquivo de entrada.

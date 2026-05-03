"""
Timesheet Analyzer — Desafio UnMEP Dev Jr.
Lê o data.json, processa os registros e gera o result.json.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ARQUIVO_ENTRADA = Path("/app/data.json")
ARQUIVO_SAIDA   = Path("/app/result.json")


def carregar_registros(caminho: Path) -> list:
    with caminho.open(encoding="utf-8") as f:
        return json.load(f)


def filtrar_registros(registros: list) -> tuple:
    # separa os válidos dos inválidos (minutes <= 0 vai fora)
    validos  = []
    ignorados = 0

    for r in registros:
        minutos = r.get("minutes")
        if isinstance(minutos, (int, float)) and minutos > 0:
            validos.append(r)
        else:
            ignorados += 1

    return validos, ignorados


def agregar_tarefas(validos: list) -> tuple:
    # soma os minutos por tarefa e guarda o nome
    minutos_por_tarefa = defaultdict(int)
    nomes_tarefa       = {}

    for r in validos:
        tid = r["taskId"]
        minutos_por_tarefa[tid] += r["minutes"]
        nomes_tarefa[tid]        = r["taskName"]

    return minutos_por_tarefa, nomes_tarefa


def agregar_usuarios(validos: list) -> tuple:
    # mesma ideia, mas por usuário — e ainda guarda quais tarefas cada um tocou
    minutos_por_usuario = defaultdict(int)
    nomes_usuario       = {}
    tarefas_por_usuario = defaultdict(set)

    for r in validos:
        uid = r["userId"]
        minutos_por_usuario[uid] += r["minutes"]
        nomes_usuario[uid]        = r["userName"]
        tarefas_por_usuario[uid].add(r["taskId"])

    return minutos_por_usuario, nomes_usuario, tarefas_por_usuario


def montar_lista_tarefas(minutos: dict, nomes: dict, total: int) -> list:
    # ordena por minutos desc, desempata pelo id asc
    ordenado = sorted(minutos.items(), key=lambda x: (-x[1], x[0]))

    return [
        {
            "taskId":       tid,
            "taskName":     nomes[tid],
            "totalMinutes": mins,
            "percentage":   f"{mins / total * 100:.2f}%",
        }
        for tid, mins in ordenado
    ]


def processar(registros: list) -> dict:
    validos, ignorados = filtrar_registros(registros)

    minutos_tarefa, nomes_tarefa             = agregar_tarefas(validos)
    minutos_usuario, nomes_usuario, tarefas_usuario = agregar_usuarios(validos)

    total_minutos = sum(minutos_tarefa.values())
    tarefas       = montar_lista_tarefas(minutos_tarefa, nomes_tarefa, total_minutos)

    # top 3 funcionários — mesma regra de ordenação
    top3_funcionarios = [
        {"userId": uid, "userName": nomes_usuario[uid], "totalMinutes": mins}
        for uid, mins in sorted(minutos_usuario.items(), key=lambda x: (-x[1], x[0]))[:3]
    ]

    # quem trabalhou em mais tarefas distintas (empate: menor userId ganha)
    uid_destaque = min(tarefas_usuario, key=lambda uid: (-len(tarefas_usuario[uid]), uid))

    return {
        "totalMinutes": total_minutos,
        "tasks":        tarefas,
        "mostWorkedTask": tarefas[0],
        "top3TasksPercentage": [
            {"taskId": t["taskId"], "taskName": t["taskName"], "percentage": t["percentage"]}
            for t in tarefas[:3]
        ],
        "top3Employees": top3_funcionarios,
        "mostDistinctUserOnTasks": {
            "userId":        uid_destaque,
            "userName":      nomes_usuario[uid_destaque],
            "distinctTasks": len(tarefas_usuario[uid_destaque]),
            "taskIds":       sorted(tarefas_usuario[uid_destaque]),
        },
        "ignoredRecords": ignorados,
    }


def main() -> None:
    if not ARQUIVO_ENTRADA.exists():
        print(f"[ERRO] Arquivo não encontrado: {ARQUIVO_ENTRADA}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Lendo {ARQUIVO_ENTRADA} ...")
    registros = carregar_registros(ARQUIVO_ENTRADA)
    print(f"[INFO] {len(registros)} registros carregados")

    resultado = processar(registros)

    validos_count = len(registros) - resultado["ignoredRecords"]
    print(f"[INFO] Válidos: {validos_count} | Ignorados: {resultado['ignoredRecords']}")
    print(f"[INFO] Total de minutos: {resultado['totalMinutes']}")
    print(f"[INFO] Tarefa mais trabalhada: {resultado['mostWorkedTask']['taskName']} ({resultado['mostWorkedTask']['totalMinutes']} min)")
    print(f"[INFO] Funcionário top: {resultado['top3Employees'][0]['userName']} ({resultado['top3Employees'][0]['totalMinutes']} min)")

    ARQUIVO_SAIDA.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK]  result.json salvo em {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()

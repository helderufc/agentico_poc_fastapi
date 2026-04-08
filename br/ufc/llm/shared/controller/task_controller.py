from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from br.ufc.llm.shared.service.celery_app import celery_app
from br.ufc.llm.shared.domain.resposta_padrao import RespostaPadrao

router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.get("/tasks/{task_id}")
async def consultar_task(task_id: str):
    """Consulta o status e resultado de uma task assíncrona."""
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return RespostaPadrao(
            data={"task_id": task_id, "status": "pendente"},
            message="Task aguardando processamento",
            status=202,
        )

    if result.state == "STARTED" or result.state == "RETRY":
        return RespostaPadrao(
            data={"task_id": task_id, "status": "processando"},
            message="Task em processamento",
            status=202,
        )

    if result.state == "SUCCESS":
        return RespostaPadrao(
            data={"task_id": task_id, "status": "concluido", "resultado": result.result},
            message="Task concluída com sucesso",
            status=200,
        )

    if result.state == "FAILURE":
        raise HTTPException(
            status_code=500,
            detail={"task_id": task_id, "status": "erro", "erro": str(result.result)},
        )

    return RespostaPadrao(
        data={"task_id": task_id, "status": result.state.lower()},
        message="Status da task",
        status=202,
    )

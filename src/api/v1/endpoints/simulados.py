from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
def generate_simulado():
    """
    Gera um simulado baseado em filtros.
    TODO: Implementar na Fase 2
    """
    return {"message": "Geração de simulado - Em desenvolvimento"}


@router.get("/{simulado_id}")
def get_simulado(simulado_id: int):
    """
    Recupera um simulado gerado.
    TODO: Implementar na Fase 2
    """
    return {"message": f"Detalhes do simulado {simulado_id} - Em desenvolvimento"}

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_questions():
    """
    Lista questões com filtros.
    TODO: Implementar na Fase 1
    """
    return {"message": "Endpoint de listagem de questões - Em desenvolvimento"}


@router.get("/{question_id}")
def get_question(question_id: int):
    """
    Retorna detalhes de uma questão específica.
    TODO: Implementar na Fase 1
    """
    return {"message": f"Detalhes da questão {question_id} - Em desenvolvimento"}


@router.post("/")
def create_question():
    """
    Cria uma nova questão.
    TODO: Implementar na Fase 1
    """
    return {"message": "Criação de questão - Em desenvolvimento"}

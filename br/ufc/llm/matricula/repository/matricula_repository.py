from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from br.ufc.llm.matricula.domain.matricula import Matricula, RespostaProva
from br.ufc.llm.curso.domain.curso import Curso
from br.ufc.llm.modulo.domain.modulo import Modulo
from br.ufc.llm.aula.domain.aula import Aula
from br.ufc.llm.prova.domain.prova import Prova


class MatriculaRepository:

    def __init__(self, session: Session):
        self.session = session

    def find_by_aluno_and_curso(self, aluno_id: int, curso_id: int) -> Optional[Matricula]:
        return (
            self.session.query(Matricula)
            .filter(Matricula.aluno_id == aluno_id, Matricula.curso_id == curso_id)
            .first()
        )

    def find_by_aluno(self, aluno_id: int) -> List[Matricula]:
        return self.session.query(Matricula).filter(Matricula.aluno_id == aluno_id).all()

    def create(self, matricula: Matricula) -> Matricula:
        self.session.add(matricula)
        self.session.commit()
        self.session.refresh(matricula)
        return matricula

    def find_cursos_publicados(self, q: Optional[str] = None) -> List[Curso]:
        query = self.session.query(Curso).filter(Curso.status == "PUBLICADO")
        if q:
            termo = f"%{q}%"
            query = query.filter(func.lower(Curso.titulo).like(func.lower(termo)))
        return query.all()

    def find_curso_publicado_by_id(self, curso_id: int) -> Optional[Curso]:
        return (
            self.session.query(Curso)
            .filter(Curso.id == curso_id, Curso.status == "PUBLICADO")
            .first()
        )

    def find_modulos_by_curso(self, curso_id: int) -> List[Modulo]:
        return (
            self.session.query(Modulo)
            .filter(Modulo.curso_id == curso_id)
            .order_by(Modulo.ordem)
            .all()
        )

    def find_aulas_by_modulo(self, modulo_id: int) -> List[Aula]:
        return (
            self.session.query(Aula)
            .filter(Aula.modulo_id == modulo_id)
            .order_by(Aula.ordem)
            .all()
        )

    def find_aula_by_id(self, aula_id: int) -> Optional[Aula]:
        return self.session.query(Aula).filter(Aula.id == aula_id).first()

    def find_prova_by_modulo(self, modulo_id: int) -> Optional[Prova]:
        return self.session.query(Prova).filter(Prova.modulo_id == modulo_id).first()

    def find_prova_by_id(self, prova_id: int) -> Optional[Prova]:
        return self.session.query(Prova).filter(Prova.id == prova_id).first()

    def find_respostas_by_aluno_and_prova(self, aluno_id: int, prova_id: int) -> List[RespostaProva]:
        return (
            self.session.query(RespostaProva)
            .filter(RespostaProva.aluno_id == aluno_id, RespostaProva.prova_id == prova_id)
            .all()
        )

    def find_resposta_by_aluno_and_pergunta(self, aluno_id: int, pergunta_id: int) -> Optional[RespostaProva]:
        return (
            self.session.query(RespostaProva)
            .filter(RespostaProva.aluno_id == aluno_id, RespostaProva.pergunta_id == pergunta_id)
            .first()
        )

    def create_resposta(self, resposta: RespostaProva) -> RespostaProva:
        self.session.add(resposta)
        self.session.commit()
        self.session.refresh(resposta)
        return resposta

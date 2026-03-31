# Regras de Negócio — PoC LLM UFC

Consulte este arquivo ao implementar services, validações e testes de integração.

- **RN01** – Conta criada sempre com status INATIVO; somente ADMIN pode ativar
- **RN02** – Professor gerencia somente os cursos que ele mesmo criou
- **RN03** – CPF e e-mail são imutáveis após o cadastro (somente leitura no perfil)
- **RN04** – Ao deletar um módulo, todos os demais módulos do curso são renumerados automaticamente
- **RN05** – Pergunta deve ter mínimo de 2 alternativas e exatamente 1 marcada como correta
- **RN06** – Curso com status RASCUNHO não é visível para alunos
- **RN07** – Arquivos aceitos nas aulas: PDF (`application/pdf`), MP4, AVI, MOV, WebM (`video/*`)
- **RN08** – Foto de perfil: formatos JPG, PNG ou GIF; dimensão mínima 200×200px
- **RN09** – Token de recuperação de senha expira em 30 minutos e só pode ser usado uma vez
- **RN10** – Categoria de curso é case-insensitive na deduplicação (`"IA" == "ia" == "Ia"`)
- **RN11** – As 3 opções de configuração da prova (respostas erradas, corretas, valores) são independentes entre si
- **RN12** – Conteúdo gerado pela IA não é persistido automaticamente; requer confirmação explícita do professor

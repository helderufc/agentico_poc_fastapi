# User Stories — PoC LLM UFC

Cada story deve gerar um ou mais testes antes da implementação (TDD).

---

## ADMIN

- **US-A01**: Como admin, quero listar todos os usuários para gerenciar acessos à plataforma
- **US-A02**: Como admin, quero ativar uma conta inativa para liberar o acesso do usuário
- **US-A03**: Como admin, quero desativar uma conta ativa para revogar o acesso

---

## PROFESSOR

### Acesso
- **US-P01**: Como professor, quero me cadastrar informando nome, CPF, e-mail, senha e perfil
- **US-P02**: Como professor, quero fazer login com e-mail e senha e receber um JWT válido
- **US-P03**: Como professor, quero recuperar minha senha via e-mail quando esquecê-la
- **US-P04**: Como professor, quero redefinir minha senha usando o token recebido por e-mail

### Perfil
- **US-P05**: Como professor, quero fazer upload da minha foto de perfil
- **US-P06**: Como professor, quero visualizar meus dados (CPF mascarado e e-mail são somente leitura)
- **US-P07**: Como professor, quero alterar minha senha informando a senha atual e a nova

### Cursos
- **US-P08**: Como professor, quero criar um curso com capa, título, categoria, descrição e carga horária
- **US-P09**: Como professor, quero configurar quais dados adicionais o aluno precisa informar para se matricular
- **US-P10**: Como professor, quero listar meus cursos separados por ativos e arquivados
- **US-P11**: Como professor, quero buscar meus cursos por texto
- **US-P12**: Como professor, quero editar os dados de um curso existente
- **US-P13**: Como professor, quero publicar um curso para torná-lo visível aos alunos
- **US-P14**: Como professor, quero arquivar um curso para removê-lo da listagem ativa
- **US-P15**: Como professor, quero excluir um curso que ainda não tem alunos matriculados

### Módulos
- **US-P16**: Como professor, quero adicionar módulos a um curso com nomes gerados automaticamente
- **US-P17**: Como professor, quero fazer upload da imagem de capa de um módulo
- **US-P18**: Como professor, quero excluir um módulo e ter os demais renumerados automaticamente
- **US-P19**: Como professor, quero reordenar os módulos de um curso

### Aulas
- **US-P20**: Como professor, quero adicionar uma aula a um módulo informando o nome
- **US-P21**: Como professor, quero fazer upload de um arquivo PDF ou vídeo para uma aula
- **US-P22**: Como professor, quero digitar conteúdo rich text (CKEditor) em uma aula
- **US-P23**: Como professor, quero ter arquivo e rich text na mesma aula simultaneamente
- **US-P24**: Como professor, quero reordenar as aulas dentro de um módulo

### Conteúdo via IA
- **US-P25**: Como professor, quero que a IA gere o conteúdo formatado da aula a partir do PDF ou texto
- **US-P26**: Como professor, quero visualizar o preview do conteúdo gerado pela IA antes de salvar
- **US-P27**: Como professor, quero confirmar o conteúdo gerado para que ele seja salvo
- **US-P28**: Como professor, quero pedir uma nova geração se não gostar do resultado

### Provas
- **US-P29**: Como professor, quero criar uma prova vinculada a um módulo
- **US-P30**: Como professor, quero adicionar perguntas à prova com alternativas e resposta correta marcada
- **US-P31**: Como professor, quero configurar a pontuação individual de cada pergunta
- **US-P32**: Como professor, quero configurar se o aluno pode ver suas respostas erradas após a prova
- **US-P33**: Como professor, quero configurar se o aluno pode ver as respostas corretas
- **US-P34**: Como professor, quero configurar se o aluno pode ver a pontuação total e por pergunta

### Quiz via IA
- **US-P35**: Como professor, quero que a IA gere perguntas para a prova lendo o conteúdo do módulo
- **US-P36**: Como professor, quero revisar e editar as perguntas geradas pela IA antes de salvar
- **US-P37**: Como professor, quero salvar as perguntas editadas na prova do módulo

---

## ALUNO (Fase 2 — não implementado ainda)

- **US-AL01**: Como aluno, quero me cadastrar e aguardar ativação da minha conta
- **US-AL02**: Como aluno, quero buscar cursos publicados na plataforma
- **US-AL03**: Como aluno, quero me matricular em um curso informando os dados exigidos pelo professor
- **US-AL04**: Como aluno, quero acessar as aulas de um módulo e ver o conteúdo formatado
- **US-AL05**: Como aluno, quero assistir videoaulas dentro da plataforma
- **US-AL06**: Como aluno, quero fazer a prova de um módulo e submeter minhas respostas
- **US-AL07**: Como aluno, quero ver meu resultado conforme as configurações definidas pelo professor

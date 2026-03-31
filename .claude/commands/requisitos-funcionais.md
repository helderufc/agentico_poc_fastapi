# Requisitos Funcionais — PoC LLM UFC (Fase 1: Professor)

## Autenticação e Usuários
- **RF01** – Cadastro com nome, CPF, e-mail, senha, perfil (PROFESSOR ou ALUNO)
- **RF02** – Login com e-mail ou nome de usuário + senha → retorna JWT (access + refresh token)
- **RF03** – Recuperação de senha via e-mail (token expira em 30 min)
- **RF04** – Admin ativa ou desativa contas de usuários
- **RF05** – Usuário com status INATIVO não consegue autenticar

## Perfil
- **RF06** – Upload de foto de perfil (JPG, PNG ou GIF — mín. 200×200px)
- **RF07** – CPF e e-mail são exibidos como somente leitura no perfil
- **RF08** – Alteração de senha requer senha atual + nova senha + confirmação da nova senha

## Cursos
- **RF09** – Professor realiza CRUD de cursos; gerencia apenas os seus próprios
- **RF10** – Upload de imagem de capa do curso
- **RF11** – Categoria salva com deduplicação case-insensitive
- **RF12** – Carga horária é texto livre (ex: "30h", "20 horas")
- **RF13** – Curso configura quais dados adicionais o aluno deve informar na matrícula: Endereço / Gênero / Idade
- **RF14** – Status do curso: RASCUNHO (padrão) / PUBLICADO / ARQUIVADO
- **RF15** – Listagem de cursos separada por status (ativos e arquivados)
- **RF16** – Editar curso carrega os dados atuais (wizard pré-preenchido)
- **RF17** – Busca de cursos por texto (título ou categoria)

## Módulos
- **RF18** – CRUD de módulos dentro de um curso
- **RF19** – Nome do módulo gerado automaticamente e de forma incremental (Módulo 01, Módulo 02...)
- **RF20** – Ao deletar módulo, os demais são renumerados automaticamente
- **RF21** – Upload de imagem de capa do módulo

## Aulas
- **RF22** – CRUD de aulas dentro de um módulo
- **RF23** – Upload de arquivo da aula (PDF ou vídeo)
- **RF24** – Campo de conteúdo rich text (HTML via CKEditor), sanitizado antes de persistir
- **RF25** – Arquivo e rich text coexistem na mesma aula

## Conteúdo Dinâmico via IA (por aula)
- **RF26** – `POST /aulas/{id}/gerar-conteudo`: lê PDF e/ou CKEditor, retorna HTML formatado pela IA
- **RF27** – O conteúdo gerado não é salvo automaticamente — professor confirma, regenera ou edita
- **RF28** – Ao confirmar, HTML é persistido no campo `conteudo_gerado` da aula

## Provas (por módulo)
- **RF29** – Criação de prova vinculada a um módulo (opcional — um módulo pode não ter prova)
- **RF30** – Prova organizada em 3 abas: Perguntas / Respostas / Configurações
- **RF31** – Cada pergunta: enunciado + mínimo de 2 alternativas + exatamente 1 marcada como correta
- **RF32** – Pontuação configurável por pergunta (padrão: 1 ponto)
- **RF33** – Aba Configurações: checkboxes independentes — Respostas erradas / Respostas corretas / Valores
- **RF34** – Aba Respostas: estatísticas de respostas dos alunos (leitura — visível após publicação)

## Quiz via IA (por módulo)
- **RF35** – `POST /modulos/{id}/prova/gerar-quiz-ia`: lê todo conteúdo legível do módulo e retorna JSON com perguntas, alternativas e resposta correta sugerida
- **RF36** – O JSON retornado não é persistido — enviado ao front para revisão e edição
- **RF37** – Se não houver conteúdo legível no módulo: retorna 422 com mensagem clara
- **RF38** – Professor edita o resultado e submete ao endpoint padrão de criação da prova

# 🤖 Review CLI: Seu Assistente Pessoal de Code Review

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Install with uv](https://img.shields.io/badge/install%20with-uv-purple)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Cansado de copiar e colar `git diff` no chat do seu Copilot ou Claude?**

O **Review CLI** é uma ferramenta simples que prepara seu projeto para automatizar o Code Review (Revisão de Código) assistido por IA.

---

## 🧐 O Problema que Resolvemos

Fazer revisão de código é essencial, mas é um processo manual. Se você usa uma IA (como GitHub Copilot, Claude, Gemini, etc.) para ajudar, seu dia-a-dia provavelmente se parece com isso:

1.  Abrir o terminal.
2.  Digitar `git diff main...minha-branch`.
3.  Copiar *tooodo* o resultado.
4.  Ir para a janela da IA, colar o código e escrever um prompt pedindo a revisão.
5.  Repetir isso para cada pequena atualização.

❌ **É um processo chato e demorado.**

---

## ✨ A Solução: `review-cli`

O **Review CLI** é uma ferramenta que você roda **apenas uma vez** no seu projeto para configurar tudo.

Ele instala os scripts e os prompts exatos que sua IA precisa. Depois de configurado, seu novo fluxo de trabalho será:

1.  **Abra o chat da sua IA** (Copilot, Claude, etc.).
2.  **Ative o prompt** que o `review-cli` criou (ex: `.github/prompts/code_review.prompt.md`).
3.  **Dê o nome da sua branch** (ex: `feature/nova-api`).

A IA irá **executar o script por você**, ler o relatório e fornecer a revisão completa.

✅ **Chega de copiar e colar!**

---

## 🚀 Guia Rápido: Do Zero à Revisão em 3 Passos

Vamos configurar seu primeiro projeto.

### Passo 1: Instale a Ferramenta

Recomendamos usar o `uv` (um instalador rápido de Python). Se você não o tem, [instale-o aqui](https://docs.astral.sh/uv/getting-started/installation/).

```bash
# Instale o review-cli globalmente
uv tool install review-cli --from git+https://github.com/oidellajulio/code-review-cli.git
````

### Passo 2: Configure seu Projeto (o `init`)

Navegue até a pasta raiz do seu projeto Git e execute:

```bash
review-cli init
```

A ferramenta fará duas perguntas simples (você pode navegar com as setas):

> Pode executar o `review-cli init` quantas vezes quiser: o CLI verifica o conteúdo atual dos scripts antes de sobrescrever e informa o hash quando tudo já está atualizado.

**1. Qual Assistente de IA você usa?** (Isso decide onde salvar o prompt).

```text
? Escolha seu Assistente de IA: (Use setas)
▶ copilot (GitHub Copilot)
  claude (Claude Code)
  gemini (Gemini CLI)
  cursor (Cursor (IDE))
  ...
```

**2. Qual o formato do Script?** (Isso detecta seu sistema operacional).

```text
? Escolha o Formato do Script: (Use setas)
  sh (POSIX Shell (Bash/Zsh) - Linux/Mac)
▶ ps (PowerShell - Windows)
```

### Passo 3: Peça a Revisão à IA (A Mágica 🪄)

Você **não precisa** executar o script manualmente. O prompt que o `review-cli` gerou já ensina a IA a fazer isso.

1.  Abra o arquivo de prompt que o `init` criou (ex: `.github/prompts/code_review.prompt.md`).
2.  No seu chat de IA (Copilot, Claude, etc.), ative o prompt (geralmente com `/` ou `@`).
3.  Quando a IA pedir os argumentos, apenas forneça o nome da sua branch: `feature/login`.

> A IA irá ler o prompt, **executar o script (`.sh` ou `.ps1`) por conta própria**, ler o arquivo `.md` gerado na pasta `diffs/` e fornecer a análise detalhada.

> Windows: se precisar rodar manualmente, utilize `powershell.exe -ExecutionPolicy Bypass -File .\.code_review\scripts\git-relatorio.ps1 <nome-da-branch>` para contornar bloqueios de ExecutionPolicy.

-----

## ⚙️ O que ele cria?

O comando `init` é seguro e não bagunça seu projeto. Ele apenas adiciona:

```text
seu-projeto/
│
├── .code_review/
│   └── scripts/
│       └── git-relatorio.sh  <-- (Ou .ps1 para Windows)
│
├── .github/
│   └── prompts/
│       └── code_review.prompt.md  <-- (Ou .claude/prompts/, etc.)
│
└── diffs/
    └── (Aqui é onde os relatórios .md aparecerão)
```

Esses arquivos são tratados de forma idempotente — se você rodar o `init` novamente e nada tiver mudado, os scripts permanecem intocados e o CLI apenas reporta o hash atual.

-----

## 🖥️ Recursos Principais

| Recurso | Descrição |
| :--- | :--- |
| **🤖 Seleção de Agente** | Salva os prompts nos diretórios corretos que cada agente espera (`.github/`, `.claude/`, `.gemini/`, etc.). |
| **💻 Cross-Platform** | Gera scripts `.sh` (Bash) para Linux/Mac e `.ps1` (PowerShell) para Windows. |
| **🖱️ Interativo** | Menus fáceis de usar com detecção automática do seu Sistema Operacional. |
| **📝 Prompts Detalhados** | O prompt gerado instrui a IA a fazer uma análise de alta qualidade, verificando segurança, performance, bugs e boas práticas. |

-----

[Reportar Bug](https://www.google.com/search?q=https://github.com/oidellajulio/code-review-cli/issues) • [Contribuir](https://www.google.com/search?q=https://github.com/oidellajulio/code-review-cli/pulls)

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "readchar",
# ]
# ///
"""
Review CLI - Ferramenta de Setup para Code Reviews Automatizados (Multi-Plataforma)

Uso:
    uvx src/code_review/__init__.py init
    uvx src/code_review/__init__.py init --here
"""

import os
import sys
import time
import platform
from pathlib import Path
from typing import Optional

import typer
import readchar
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.tree import Tree
from rich.table import Table
from typer.core import TyperGroup

# --- CONFIGURAÇÃO DOS AGENTES (Mapeamento de Pastas) ---

AGENT_CONFIG = {
    "copilot": {
        "name": "GitHub Copilot",
        "prompt_dir": ".github/prompts",
    },
    "claude": {
        "name": "Claude Code",
        "prompt_dir": ".claude/prompts", # Convenção comum, ajustável
    },
    "gemini": {
        "name": "Gemini CLI",
        "prompt_dir": ".gemini/prompts",
    },
    "cursor": {
        "name": "Cursor (IDE)",
        "prompt_dir": ".cursor/prompts",
    },
    "openai": {
        "name": "OpenAI / Codex",
        "prompt_dir": ".openai/prompts",
    },
    "generic": {
        "name": "Genérico (Outros)",
        "prompt_dir": "code_review/prompts",
    },
}

SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (Bash/Zsh) - Linux/Mac", "ps": "PowerShell - Windows"}

# --- CONTEÚDO DOS ARQUIVOS (Embedados) ---

# Script Bash (Linux/Mac)
SCRIPT_CONTENT_SH = """#!/bin/bash

# 1. Verifica se o usuário passou o nome da branch
if [ -z "$1" ]; then
  echo "❌ Erro: Você precisa fornecer o nome da branch."
  echo "Uso: ./git-relatorio.sh <nome-da-branch>"
  exit 1
fi

BRANCH_ALVO=$1
BRANCH_BASE="main" # Altere para 'master' se necessário

# --- CONFIGURAÇÃO DE DIRETÓRIO ---

# Obtém o caminho absoluto de onde ESTE script está salvo
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Salva na pasta 'diffs' dois níveis acima (sai de .code_review/scripts)
DIR_SAIDA="$SCRIPT_DIR/../../diffs"

if [ ! -d "$DIR_SAIDA" ]; then
  echo "📂 Diretório central '$DIR_SAIDA' não encontrado. Criando..."
  mkdir -p "$DIR_SAIDA"
fi

NOME_ARQUIVO_SAFE=$(echo "$BRANCH_ALVO" | tr '/' '-')
ARQUIVO_SAIDA="${DIR_SAIDA}/relatorio_diff_${NOME_ARQUIVO_SAFE}.md"

echo "🔄 Processando alterações entre '$BRANCH_BASE' e '$BRANCH_ALVO'..."

# --- GERAÇÃO DO MARKDOWN ---
{
    echo "# Relatório de Alterações: $BRANCH_ALVO"
    echo "**Projeto:** $(basename "$PWD")"
    echo "**Gerado em:** $(date)"
    echo "**Branch Base:** $BRANCH_BASE"
    echo "**Branch Alvo:** $BRANCH_ALVO"
    echo ""
    echo "---"
    echo ""
    echo "## 📂 Arquivos Alterados"
    echo ""
    git diff --name-only "origin/$BRANCH_BASE".."$BRANCH_ALVO" -- . ':(exclude)*.md' | sed 's/^/- /'
    echo ""
    echo "## 📝 Histórico de Commits"
    echo ""
    git log --no-merges --oneline "origin/$BRANCH_BASE".."$BRANCH_ALVO" | sed 's/^/- /'
    echo ""
    echo "## 💻 Detalhes do Código (Diff)"
    echo ""
    echo "\`\`\`diff"
    git diff "origin/$BRANCH_BASE"..."$BRANCH_ALVO" -- . ':(exclude)*.md' | grep -v '^-[^-]'
    echo "\`\`\`"
} > "$ARQUIVO_SAIDA"

echo "✅ Sucesso! O arquivo foi salvo em: $ARQUIVO_SAIDA"
"""

# Script PowerShell (Windows)
SCRIPT_CONTENT_PS = """<#
.SYNOPSIS
    Gera um relatório Markdown de diff entre branches.
.DESCRIPTION
    Uso: .\\git-relatorio.ps1 "feature/minha-branch"
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$BranchAlvo,
    [string]$BranchBase = "main"
)

$ErrorActionPreference = "Stop"

# --- CONFIGURAÇÃO DE DIRETÓRIO ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
# Navega dois níveis acima (.code_review/scripts/ -> raiz -> diffs)
$DirSaida = Join-Path $ScriptDir "..\\..\\diffs"

if (-not (Test-Path $DirSaida)) {
    Write-Host "📂 Diretório central '$DirSaida' não encontrado. Criando..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $DirSaida | Out-Null
}

$NomeArquivoSafe = $BranchAlvo -replace '[/\\:]', '-'
$ArquivoSaida = Join-Path $DirSaida "relatorio_diff_$NomeArquivoSafe.md"

Write-Host "🔄 Processando alterações entre '$BranchBase' e '$BranchAlvo'..." -ForegroundColor Yellow

# --- GERAÇÃO DO MARKDOWN ---
$Encoding = "UTF8" # Garante caracteres corretos

try {
    $Content = @()
    $Content += "# Relatório de Alterações: $BranchAlvo"
    $Content += "**Projeto:** $(Split-Path -Leaf (Get-Location))"
    $Content += "**Gerado em:** $(Get-Date)"
    $Content += "**Branch Base:** $BranchBase"
    $Content += "**Branch Alvo:** $BranchAlvo"
    $Content += ""
    $Content += "---"
    $Content += ""
    $Content += "## 📂 Arquivos Alterados"
    $Content += ""
    $Content += (git diff --name-only "origin/$BranchBase..$BranchAlvo" -- . ':(exclude)*.md') -replace '^', '- '
    $Content += ""
    $Content += "## 📝 Histórico de Commits"
    $Content += ""
    $Content += (git log --no-merges --oneline "origin/$BranchBase..$BranchAlvo") -replace '^', '- '
    $Content += ""
    $Content += "## 💻 Detalhes do Código (Diff)"
    $Content += ""
    $Content += "```diff"
    $Content += (git diff "origin/$BranchBase...$BranchAlvo" -- . ':(exclude)*.md') -notmatch '^-[^-]'
    $Content += "```"

    $Content | Out-File -FilePath $ArquivoSaida -Encoding utf8
    
    Write-Host "✅ Sucesso! O arquivo foi salvo em: $ArquivoSaida" -ForegroundColor Green
}
catch {
    Write-Error "Falha ao gerar relatório: $_"
}
"""

PROMPT_CONTENT_TEMPLATE = """---
description: Realiza uma revisão de código detalhada e construtiva com base em um diff de git.
tags: [code-review, git, quality, best-practices]
---

## Objetivo
Você é um Engenheiro de Software Sênior especializado em revisão de código. Seu objetivo é analisar um `git diff` fornecido pelo usuário, identificar problemas e sugerir melhorias claras e acionáveis.

## Instruções de Execução (Para o Copiloto)

**IMPORTANTE:** Quando o usuário fornecer o nome de uma branch como argumento. Você deve primeiro gerar o relatório de diff antes de analisá-lo. Se o usuário não fornecer uma branch, use a branch atual. Para identificar a branch atual, você pode usar o comando `git rev-parse --abbrev-ref HEAD`.

1.  **Execute o Script de Relatório:**
    Execute o script de relatório para gerar o diff. O comando (a partir da raiz do projeto) é:
    `{SCRIPT_COMMAND_PLACEHOLDER}`

2.  **Localize o Relatório:** O script acima salvará um arquivo em `./diffs/relatorio_diff_<nome-da-branch-formatado>.md`.

3.  **Analise o Conteúdo:** Leia e analise o conteúdo completo desse arquivo `.md`. O diff estará dentro dele.

4.  **Forneça a Revisão:** Com base no diff, forneça sua revisão de código seguindo os critérios abaixo.

5.  **Limpeza (Opcional):** Após a revisão, você pode sugerir a remoção do arquivo de diff gerado para manter o repositório limpo.

---

## Critérios de Revisão de Código

Por favor, analise o diff fornecido e estruture seu feedback abordando os seguintes pontos:

### 1. Visão Geral
* (Forneça um breve resumo das mudanças: O que esta branch parece estar fazendo?)

### 2. Qualidade e Legibilidade
* **Clareza:** O código é fácil de entender?
* **Nomenclatura:** Nomes de variáveis, funções e classes são claros e descritivos?
* **Complexidade:** Existem funções ou métodos excessivamente longos ou complexos (alta complexidade ciclomática)? Sugira refatorações se necessário.

### 3. Funcionalidade e Lógica
* **Bugs Potenciais:** Você identifica alguma lógica falha, condição de borda (edge case) não tratada ou potencial para `null reference` / `undefined`?
* **Eficiência:** Existem loops ineficientes, consultas desnecessárias ao banco de dados ou problemas de performance óbvios?

### 4. Boas Práticas e Princípios
* **SOLID/DRY:** O código segue princípios como DRY (Don't Repeat Yourself) e SOLID?
* **Segurança:** Alguma alteração introduz vulnerabilidades óbvias (ex: SQL Injection, XSS, exposição de chaves)?
* **Testabilidade:** As mudanças são fáceis de testar? O código de teste (se incluído no diff) é adequado?

### 5. Consistência de Estilo
* O código segue o estilo (linting) e os padrões do restante do projeto (visíveis no diff)?

### 6. Sugestões e Comentários
* (Liste pontos específicos de melhoria, referenciando o arquivo e a linha, se possível.)

## Exemplo de Resposta (Após a execução do script)

```markdown
(Conteúdo do arquivo `relatorio_diff_feature-xyz.md` carregado e analisado)

---

## Revisão de Código: `feature-xyz`

### 1. Visão Geral
Esta branch parece adicionar um novo endpoint de API para `/users/{{id}}` e refatorar o serviço de autenticação.

### 2. Qualidade e Legibilidade
* **Clareza:** Boa.
* **Nomenclatura:** `src/services/auth.py` -> A função `handle_user_data` poderia ser renomeada para `process_user_login`, pois parece ser mais específica.

### 3. Funcionalidade e Lógica
* **Bug Potencial:** `src/api/endpoints.py`, Linha 42: O `if user:` não trata o caso de `user` ser encontrado mas estar inativo. Devemos verificar `if user and user.is_active:`.

... (etc)
```

## Input do Usuário (Nome da Branch)
```text
$ARGUMENTS
```

## Resposta da IA (Inicie aqui)
```text
(Primeiro, execute o script para gerar o diff...)
(Depois, forneça a análise...)
```
"""

# --- UI COMPONENTS & UTILS ---

BANNER = """
██████╗ ███████╗██╗   ██╗██╗███████╗██╗    ██╗
██╔══██╗██╔════╝██║   ██║██║██╔════╝██║    ██║
██████╔╝█████╗  ██║   ██║██║█████╗  ██║ █╗ ██║
██╔══██╗██╔══╝  ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
██║  ██║███████╗ ╚████╔╝ ██║███████╗╚███╔███╔╝
╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝ 
"""

TAGLINE = "Automated Code Review Bootstrap Tool (Multi-Agent & Cross-Platform)"

console = Console()

class StepTracker:
    """Rastreia e renderiza passos hierárquicos (estilo Spec Kit)."""
    def __init__(self, title: str):
        self.title = title
        self.steps = []
        self._refresh_cb = None

    def attach_refresh(self, cb):
        self._refresh_cb = cb

    def add(self, key: str, label: str):
        if key not in [s["key"] for s in self.steps]:
            self.steps.append({"key": key, "label": label, "status": "pending", "detail": ""})
            self._maybe_refresh()

    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)

    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)

    def error(self, key: str, detail: str = ""):
        self._update(key, status="error", detail=detail)

    def _update(self, key: str, status: str, detail: str):
        for s in self.steps:
            if s["key"] == key:
                s["status"] = status
                if detail:
                    s["detail"] = detail
                self._maybe_refresh()
                return
        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()

    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass

    def render(self):
        tree = Tree(f"[cyan]{self.title}[/cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""
            status = step["status"]
            
            if status == "done": symbol = "[green]●[/green]"
            elif status == "pending": symbol = "[green dim]○[/green dim]"
            elif status == "running": symbol = "[cyan]○[/cyan]"
            elif status == "error": symbol = "[red]●[/red]"
            else: symbol = " "

            style = "white" if status != "pending" else "bright_black"
            line = f"{symbol} [{style}]{label}[/{style}]"
            if detail_text:
                line += f" [bright_black]({detail_text})[/bright_black]"
            tree.add(line)
        return tree

def get_key():
    """Obtém um único toque de tecla (multi-plataforma)."""
    key = readchar.readkey()
    if key == readchar.key.UP or key == readchar.key.CTRL_P: return 'up'
    if key == readchar.key.DOWN or key == readchar.key.CTRL_N: return 'down'
    if key == readchar.key.ENTER: return 'enter'
    if key == readchar.key.ESC: return 'escape'
    if key == readchar.key.CTRL_C: raise KeyboardInterrupt
    return key

def select_with_arrows(options: dict, prompt_text: str = "Select an option", default_key: str = None) -> str:
    """Seleção interativa usando setas (estilo Spec Kit)."""
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0

    selected_key = None

    def create_selection_panel():
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")

        for i, key in enumerate(option_keys):
            # Obtém o nome (seja de um dict ou de uma string simples)
            option_display_name = options[key]['name'] if isinstance(options[key], dict) else options[key]
            
            if i == selected_index:
                table.add_row("▶", f"[cyan]{key}[/cyan] [dim]({option_display_name})[/dim]")
            else:
                table.add_row(" ", f"[cyan]{key}[/cyan] [dim]({option_display_name})[/dim]")

        table.add_row("", "")
        table.add_row("", "[dim]Use ↑/↓ para navegar, Enter para selecionar[/dim]")

        return Panel(
            table,
            title=f"[bold]{prompt_text}[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )

    console.print()
    with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
        while True:
            live.update(create_selection_panel(), refresh=True)
            try:
                key = get_key()
                if key == 'up':
                    selected_index = (selected_index - 1) % len(option_keys)
                elif key == 'down':
                    selected_index = (selected_index + 1) % len(option_keys)
                elif key == 'enter':
                    selected_key = option_keys[selected_index]
                    break
                elif key == 'escape':
                    console.print("[yellow]Seleção cancelada.[/yellow]")
                    raise typer.Exit(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Seleção cancelada.[/yellow]")
                raise typer.Exit(1)
    
    return selected_key

class BannerGroup(TyperGroup):
    def format_help(self, ctx, formatter):
        show_banner()
        super().format_help(ctx, formatter)

app = typer.Typer(
    name="review-cli",
    help="Ferramenta de Setup para Ambiente de Review",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

def show_banner():
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_blue", "blue", "cyan", "bright_cyan"]
    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)
    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()

@app.callback()
def callback(ctx: typer.Context):
    """Exibe o banner se nenhum comando for invocado."""
    if ctx.invoked_subcommand is None:
        show_banner()
        console.print(Align.center("[dim]Execute 'review-cli init' para começar.[/dim]"))
        console.print()

def create_file(path: Path, content: str, tracker: StepTracker, step_key: str, make_executable: bool = False):
    """Helper para criar arquivos e atualizar o tracker."""
    try:
        tracker.start(step_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Normaliza quebras de linha para Unix (LF)
        content = content.replace('\r\n', '\n')
        
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
            
        # Torna executável (Linux/Mac)
        if make_executable and os.name != 'nt':
            st = os.stat(path)
            os.chmod(path, st.st_mode | 0o111) # Adiciona permissão de execução
            tracker.complete(step_key, f"criado & chmod +x")
        else:
            tracker.complete(step_key, "criado")
            
    except Exception as e:
        tracker.error(step_key, str(e))
        raise e

@app.command()
def init(
    ai: str = typer.Option(None, "--ai", help="Assistente de IA (copilot, claude, gemini, etc)"),
    script_type: str = typer.Option(None, "--script", help="Tipo de script (sh ou ps)"),
    here: bool = typer.Option(False, "--here", help="Inicializar no diretório atual (flag legada)"),
):
    """
    Inicializa a estrutura do Code Review.
    Suporta múltiplos agentes e SOs.
    """
    show_banner()
    
    root_path = Path.cwd()
    
    # 1. Seleciona IA
    if ai:
        if ai not in AGENT_CONFIG:
            console.print(f"[red]Erro: IA inválida '{ai}'.[/red] Opções: {', '.join(AGENT_CONFIG.keys())}")
            raise typer.Exit(1)
        selected_ai = ai
    else:
        # Modo interativo se stdin for um TTY
        if not sys.stdin.isatty():
            selected_ai = "copilot" # Default para ambientes não interativos
            console.print("[dim]Ambiente não interativo, usando 'copilot' como padrão.[/dim]")
        else:
            selected_ai = select_with_arrows(AGENT_CONFIG, "Escolha seu Assistente de IA", default_key="copilot")
    
    # 2. Seleciona Tipo de Script
    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(f"[red]Erro: Tipo de script inválido '{script_type}'.[/red] Opções: {', '.join(SCRIPT_TYPE_CHOICES.keys())}")
            raise typer.Exit(1)
        selected_script = script_type
    else:
        # Auto-detecta padrão baseado no SO
        default_script = "ps" if platform.system() == "Windows" else "sh"
        if not sys.stdin.isatty():
            selected_script = default_script
            console.print(f"[dim]Ambiente não interativo, usando '{default_script}' como padrão.[/dim]")
        else:
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Escolha o Formato do Script", default_key=default_script)

    console.print(f"[cyan]Alvo:[/cyan] {AGENT_CONFIG[selected_ai]['name']}")
    console.print(f"[cyan]Script:[/cyan] {selected_script.upper()}\n")

    # 3. Setup do Tracker
    tracker = StepTracker("Inicializando Review Kit")
    tracker.add("dirs", "Criar estrutura de diretórios")
    tracker.add("script", f"Gerar script {selected_script.upper()}")
    tracker.add("prompt", f"Gerar Prompt para {selected_ai}")
    
    with Live(tracker.render(), console=console, refresh_per_second=8, transient=False) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        
        # Caminhos
        script_dir = root_path / ".code_review" / "scripts"
        prompt_relative_path = AGENT_CONFIG[selected_ai]["prompt_dir"]
        prompt_dir = root_path / prompt_relative_path
        
        # Passo 1: Diretórios
        tracker.start("dirs")
        try:
            script_dir.mkdir(parents=True, exist_ok=True)
            prompt_dir.mkdir(parents=True, exist_ok=True)
            tracker.complete("dirs", "pronto")
        except Exception as e:
            tracker.error("dirs", str(e))
            return

        time.sleep(0.3) # Pausa estética

        # Passo 2: Script
        if selected_script == "sh":
            script_path = script_dir / "git-relatorio.sh"
            content = SCRIPT_CONTENT_SH
            create_file(script_path, content, tracker, "script", make_executable=True)
            
            # Define o comando dinâmico para o prompt (relativo ao root_path)
            rel_script_path = script_path.relative_to(root_path)
            script_command = f"./{rel_script_path.as_posix()} <nome-da-branch-fornecida>"
        else:
            script_path = script_dir / "git-relatorio.ps1"
            content = SCRIPT_CONTENT_PS
            create_file(script_path, content, tracker, "script", make_executable=False)
            
            # Define o comando dinâmico para o prompt (relativo ao root_path)
            rel_script_path = script_path.relative_to(root_path)
            
            # Correção: Monta o comando do PowerShell fora do f-string para evitar erro de '\'
            # Primeiro, obtém o caminho formatado para Windows
            script_path_str = rel_script_path.as_posix().replace('/', '\\')
            # Então, insere a string simples no f-string
            script_command = f".\\{script_path_str} <nome-da-branch-fornecida>"

        time.sleep(0.3)

        # Passo 3: Prompt
        prompt_filename = "code_review.prompt.md"
        prompt_path = prompt_dir / prompt_filename
        
        # Gera o conteúdo do prompt dinamicamente
        final_prompt_content = PROMPT_CONTENT_TEMPLATE.format(
            SCRIPT_COMMAND_PLACEHOLDER=script_command
        )
        
        create_file(prompt_path, final_prompt_content, tracker, "prompt")

    # Sumário Final
    console.print("\n[bold green]✨ Ambiente pronto![/bold green]")
    
    rel_script = script_path.relative_to(root_path)
    rel_prompt = prompt_path.relative_to(root_path)
    
    # Define o comando de execução baseado no SO/script
    # Correção: A lógica do prefixo foi movida para fora do f-string para evitar o SyntaxError com '\'
    prefix = "./" if selected_script == "sh" else ".\\"
    run_command = f"{prefix}{rel_script} feature-branch"

    console.print(Panel(
        f"Script: [cyan]{rel_script}[/cyan]\n"
        f"Prompt: [cyan]{rel_prompt}[/cyan]\n\n"
        f"[dim]Para executar (exemplo):[/dim]\n"
        f"[cyan]{run_command}[/cyan]",
        title="Próximos Passos",
        border_style="green"
    ))

def main():
    app()

if __name__ == "__main__":
    main()
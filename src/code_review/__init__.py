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
Review CLI - Setup tool for Automated Code Reviews

Usage:
    uvx review-cli.py init
    uvx review-cli.py init --here
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.tree import Tree
from typer.core import TyperGroup

# --- CONTEÚDO DOS ARQUIVOS (Embedados) ---

# O script Bash que criamos anteriormente
SCRIPT_CONTENT = """#!/bin/bash

# 1. Verifica se o usuário passou o nome da branch
if [ -z "$1" ]; then
  echo "❌ Erro: Você precisa fornecer o nome da branch."
  echo "Uso: git-relatorio <nome-da-branch>"
  exit 1
fi

BRANCH_ALVO=$1
BRANCH_BASE="main" # Altere para 'master' se necessário
DATA_HOJE=$(date +"%Y-%m-%d_%H-%M")

# --- CONFIGURAÇÃO DE DIRETÓRIO (Alterada) ---

# Obtém o caminho absoluto de onde ESTE script está salvo
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define o diretório de saída relativo à localização do script
# ".." significa um nível acima da pasta onde o script está.
# Se o script está em ~/scripts, a pasta será ~/diffs
DIR_SAIDA="$SCRIPT_DIR/../diffs"

# Verifica se o diretório existe, se não, cria
if [ ! -d "$DIR_SAIDA" ]; then
  echo "📂 Diretório central '$DIR_SAIDA' não encontrado. Criando..."
  mkdir -p "$DIR_SAIDA"
fi

# Tratamento para nome do arquivo
NOME_ARQUIVO_SAFE=$(echo "$BRANCH_ALVO" | tr '/' '-')
ARQUIVO_SAIDA="${DIR_SAIDA}/relatorio_diff_${NOME_ARQUIVO_SAFE}.md"

echo "🔄 Processando alterações entre '$BRANCH_BASE' e '$BRANCH_ALVO'..."

# --- INÍCIO DA GERAÇÃO DO ARQUIVO ---

# Cabeçalho do Markdown
echo "# Relatório de Alterações: $BRANCH_ALVO" > "$ARQUIVO_SAIDA"
echo "**Projeto (Pasta):** $(basename "$PWD")" >> "$ARQUIVO_SAIDA"
echo "**Gerado em:** $(date)" >> "$ARQUIVO_SAIDA"
echo "**Branch Base:** $BRANCH_BASE" >> "$ARQUIVO_SAIDA"
echo "**Branch Alvo:** $BRANCH_ALVO" >> "$ARQUIVO_SAIDA"
echo "" >> "$ARQUIVO_SAIDA"

echo "---" >> "$ARQUIVO_SAIDA"
echo "" >> "$ARQUIVO_SAIDA"

# Seção 1: Lista de Arquivos
echo "## 📂 Arquivos Alterados" >> "$ARQUIVO_SAIDA"
echo "" >> "$ARQUIVO_SAIDA"
git diff --name-only "$BRANCH_BASE".."$BRANCH_ALVO" | sed 's/^/- /' >> "$ARQUIVO_SAIDA"
echo "" >> "$ARQUIVO_SAIDA"

# Seção 2: Lista de Commits
echo "## 📝 Histórico de Commits (Exclusivos desta Branch)" >> "$ARQUIVO_SAIDA"
echo "" >> "$ARQUIVO_SAIDA"
git log --no-merges --oneline "$BRANCH_BASE".."$BRANCH_ALVO" | sed 's/^/- /' >> "$ARQUIVO_SAIDA"
echo "" >> "$ARQUIVO_SAIDA"

# Seção 3: Diff do Código
echo "## 💻 Detalhes do Código (Diff)" >> "$ARQUIVO_SAIDA"
echo "Abaixo estão as alterações linha a linha:" >> "$ARQUIVO_SAIDA"
echo "" >> "$ARQUIVO_SAIDA"
echo "\`\`\`diff" >> "$ARQUIVO_SAIDA"
git diff "$BRANCH_BASE"..."$BRANCH_ALVO" >> "$ARQUIVO_SAIDA"
echo "\`\`\`" >> "$ARQUIVO_SAIDA"

echo "✅ Sucesso! O arquivo foi salvo em: $ARQUIVO_SAIDA"
"""

# O Prompt para o Agente de IA
PROMPT_CONTENT = """---
description: Faz uma revisão de código para as alterações fornecidas, garantindo qualidade, consistência e aderência às melhores práticas.
---

## User Input
```text
$ARGUMENTS
```

## Code Review
Por favor, realize uma revisão de código detalhada para as alterações fornecidas. Verifique os seguintes aspectos:
1. **Qualidade do Código**: O código segue as melhores práticas de codificação? Está limpo, legível e bem estruturado?
2. **Consistência**: O código é consistente com o estilo e padrões do projeto
3. **Funcionalidade**: As alterações implementam corretamente a funcionalidade pretendida? Há bugs ou problemas potenciais?
4. **Desempenho**: O código é eficiente? Existem melhorias de desempenho que
podem ser feitas?
5. **Segurança**: O código é seguro? Existem vulnerabilidades ou riscos potenciais
6. **Testabilidade**: O código é testável? Existem testes adequados para as novas funcionalidades?
7. **Principios SOLID**: O código segue os princípios SOLID de design orientado a objetos?
8. Code Smells: Há algum cheiro de código que precise ser abordado?
Forneça feedback específico e sugestões de melhorias, se necessário. Seja construtivo e detalhado em sua revisão.

Etapas de execução:
1. Execute o script `.code_review/scripts/gerar_diff.sh <branch_name>` para gerar o diff entre os branches.
2. Revise o diff gerado no arquivo markdown localizado em .code_review/diffs/relatorio_diff_<branch_name>.md
3. Forneça um feedback detalhado com base nos aspectos listados acima.
4. Se tudo estiver em ordem, envie uma mensagem para o Discord indicando que o código está aprovado.
5. Por fim remova o arquivo de diff para manter o repositório limpo.

Após revisar o diff gerado, aqui está o feedback detalhado:
```text
$FEEDBACK
```

"""

# --- UI COMPONENTS (Copiado e adaptado do Spec Kit) ---

BANNER = """
██████╗ ███████╗██╗   ██╗██╗███████╗██╗    ██╗
██╔══██╗██╔════╝██║   ██║██║██╔════╝██║    ██║
██████╔╝█████╗  ██║   ██║██║█████╗  ██║ █╗ ██║
██╔══██╗██╔══╝  ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
██║  ██║███████╗ ╚████╔╝ ██║███████╗╚███╔███╔╝
╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝ 
"""

TAGLINE = "Automated Code Review Bootstrap Tool"

console = Console()

class StepTracker:
    """Track and render hierarchical steps without emojis."""
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

class BannerGroup(TyperGroup):
    def format_help(self, ctx, formatter):
        show_banner()
        super().format_help(ctx, formatter)

app = typer.Typer(
    name="review-cli",
    help="Setup tool for Review Environment",
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
    if ctx.invoked_subcommand is None:
        show_banner()

def create_file(path: Path, content: str, tracker: StepTracker, step_key: str, make_executable: bool = False):
    """Helper to create files and update tracker."""
    try:
        tracker.start(step_key)
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Make executable if requested
        if make_executable and os.name != 'nt':
            st = os.stat(path)
            os.chmod(path, st.st_mode | 0o111)
            tracker.complete(step_key, f"created & chmod +x")
        else:
            tracker.complete(step_key, "created")
            
    except Exception as e:
        tracker.error(step_key, str(e))
        raise e

@app.command()
def init(
    here: bool = typer.Option(False, "--here", help="Initialize in current dir"),
):
    """
    Initialize the Code Review structure.
    
    Creates:
    - code_review/scripts/git-relatorio.sh
    - .github/prompts/code_review.prompt.md
    """
    show_banner()
    
    root_path = Path.cwd()
    console.print(f"[dim]Working path: {root_path}[/dim]\n")

    tracker = StepTracker("Initializing Code Review Kit")
    
    # Define steps
    tracker.add("dirs", "Create directory structure")
    tracker.add("script", "Generate scripts")
    tracker.add("prompt", "Generate prompts")
    tracker.add("final", "Finalize setup")

    with Live(tracker.render(), console=console, refresh_per_second=8, transient=False) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        
        # 1. Directories
        tracker.start("dirs")
        script_dir = root_path / ".code_review" / "scripts"
        prompt_dir = root_path / ".github" / "prompts"
        
        try:
            script_dir.mkdir(parents=True, exist_ok=True)
            prompt_dir.mkdir(parents=True, exist_ok=True)
            tracker.complete("dirs", "directories ready")
        except Exception as e:
            tracker.error("dirs", str(e))
            return

        time.sleep(0.5) # UI aesthetic pause

        # 2. Create Script
        script_path = script_dir / "gerar_diff.sh"
        create_file(script_path, SCRIPT_CONTENT, tracker, "script", make_executable=True)
        
        time.sleep(0.3)

        # 3. Create Prompt
        prompt_path = prompt_dir / "code_review.prompt.md"
        create_file(prompt_path, PROMPT_CONTENT, tracker, "prompt")

        tracker.complete("final", "setup complete")

    console.print("\n[bold green]✨ Environment ready![/bold green]")
    console.print(f"Script: [cyan]{script_path.relative_to(root_path)}[/cyan]")
    console.print(f"Prompt: [cyan]{prompt_path.relative_to(root_path)}[/cyan]")

if __name__ == "__main__":
    app()

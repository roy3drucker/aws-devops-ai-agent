import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Ensure we can import from current directory
sys.path.append(os.getcwd())

from orchestrator import create_orchestrator

def main():
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]AWS DevOps Assistant - Interactive Mode[/bold blue]",
        subtitle="Type 'exit' or 'quit' to stop"
    ))
    
    orchestrator = create_orchestrator()
    
    while True:
        user_input = Prompt.ask("\n[bold green]You[/bold green]")
        
        if user_input.lower() in ['exit', 'quit']:
            console.print("[yellow]Goodbye![/yellow]")
            break
        
        with console.status("[bold yellow]🤖 Orchestrator is thinking...[/bold yellow]", spinner="dots"):
            try:
                response = orchestrator.invoke(user_input)
                console.print("\n[bold cyan]Assistant:[/bold cyan]")
                console.print(Panel(response))
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()

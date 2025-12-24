"""Typer CLI interface for QuickSpin AI."""

import asyncio
import json
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from app.core.config import get_settings

app = typer.Typer(
    name="quickspin-ai",
    help="QuickSpin AI - Intelligent microservices management assistant",
)
console = Console()


class CLIClient:
    """Async HTTP client for CLI commands."""

    def __init__(self, api_url: str, token: str) -> None:
        """
        Initialize CLI client.

        Args:
            api_url: API base URL
            token: User JWT token
        """
        self.api_url = api_url
        self.token = token
        self.client = httpx.AsyncClient(
            base_url=api_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    async def chat(self, message: str, conversation_id: Optional[str] = None) -> dict:
        """
        Send chat message to API.

        Args:
            message: User message
            conversation_id: Optional conversation ID

        Returns:
            API response dictionary
        """
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = await self.client.post("/api/v1/chat", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_recommendations(self) -> dict:
        """
        Get cost optimization recommendations.

        Returns:
            API response dictionary
        """
        response = await self.client.get("/api/v1/recommendations")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


@app.command()
def chat(
    token: str = typer.Option(..., "--token", "-t", help="QuickSpin JWT token"),
    api_url: str = typer.Option(
        "http://localhost:8000",
        "--api-url",
        help="QuickSpin AI API URL",
    ),
) -> None:
    """
    Start interactive chat session with QuickSpin AI.

    Args:
        token: User JWT token
        api_url: API base URL
    """
    console.print("\n[bold cyan]QuickSpin AI - Interactive Chat[/bold cyan]\n")
    console.print("Type 'exit' or 'quit' to end the session.\n")

    async def chat_loop() -> None:
        """Async chat loop."""
        client = CLIClient(api_url, token)
        conversation_id: Optional[str] = None

        try:
            while True:
                # Get user input
                message = Prompt.ask("[bold green]You[/bold green]")

                if message.lower() in ["exit", "quit"]:
                    console.print("\n[yellow]Goodbye![/yellow]\n")
                    break

                # Send to API
                try:
                    response = await client.chat(message, conversation_id)
                    conversation_id = response["conversation_id"]

                    # Display response
                    console.print("\n[bold blue]QuickSpin AI[/bold blue]")
                    console.print(Markdown(response["message"]))
                    console.print()

                    # Show actions if any
                    if response.get("actions"):
                        console.print("[dim]Suggested actions:[/dim]")
                        for action in response["actions"]:
                            console.print(f"  - {action.get('type', 'unknown')}")
                        console.print()

                except httpx.HTTPError as e:
                    console.print(f"[red]Error: {e}[/red]\n")

        finally:
            await client.close()

    asyncio.run(chat_loop())


@app.command()
def recommend(
    token: str = typer.Option(..., "--token", "-t", help="QuickSpin JWT token"),
    api_url: str = typer.Option(
        "http://localhost:8000",
        "--api-url",
        help="QuickSpin AI API URL",
    ),
) -> None:
    """
    Get cost optimization recommendations.

    Args:
        token: User JWT token
        api_url: API base URL
    """
    console.print("\n[bold cyan]QuickSpin AI - Cost Optimization[/bold cyan]\n")

    async def get_recommendations_async() -> None:
        """Async recommendations fetch."""
        client = CLIClient(api_url, token)

        try:
            response = await client.get_recommendations()

            # Display cost analysis
            if response.get("cost_analysis"):
                cost_analysis = response["cost_analysis"]
                console.print("[bold]Current Cost Summary[/bold]")
                console.print(
                    f"Total Monthly Cost: [green]${cost_analysis['total_monthly_cost']:.2f}[/green]"
                )
                console.print(
                    f"Optimization Potential: [yellow]${cost_analysis['optimization_potential']:.2f}[/yellow]\n"
                )

                # Breakdown table
                table = Table(title="Cost Breakdown by Service Type")
                table.add_column("Service Type", style="cyan")
                table.add_column("Monthly Cost", style="green", justify="right")

                for service_type, cost in cost_analysis["breakdown_by_service_type"].items():
                    table.add_row(service_type, f"${cost:.2f}")

                console.print(table)
                console.print()

            # Display recommendations
            if response.get("recommendations"):
                console.print("[bold]Recommendations[/bold]\n")
                for rec in response["recommendations"]:
                    console.print(f"[{rec['priority'].upper()}] {rec['title']}")
                    console.print(f"  {rec['description']}")
                    console.print(
                        f"  Potential Savings: [green]${rec['estimated_savings_monthly']:.2f}/month[/green]"
                    )
                    console.print()
            else:
                console.print("[green]No recommendations - your setup is optimized![/green]\n")

        except httpx.HTTPError as e:
            console.print(f"[red]Error: {e}[/red]\n")
        finally:
            await client.close()

    asyncio.run(get_recommendations_async())


@app.command()
def version() -> None:
    """Show version information."""
    console.print("\n[bold cyan]QuickSpin AI CLI[/bold cyan]")
    console.print("Version: 0.1.0\n")


if __name__ == "__main__":
    app()

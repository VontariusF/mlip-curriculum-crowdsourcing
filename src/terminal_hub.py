"""
Real-time Terminal Hub using Rich
Displays live progress, agent status, and system metrics
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.logging import RichHandler
import logging

class TerminalHub:
    """Real-time terminal dashboard for system monitoring"""
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        
        # System state
        self.current_batch = 0
        self.batch_status = "Initializing..."
        self.agent_status = {
            "scraping": {"status": "Idle", "progress": 0, "results": 0},
            "classification": {"status": "Idle", "progress": 0, "results": 0}
        }
        self.statistics = {
            "total_resources": 0,
            "total_duplicates": 0,
            "current_batch": 0,
            "success_rate": 0.0
        }
        self.activity_log = []
        self.error_log = []
        
        # Progress tracking
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        
        self.is_running = False
        self.live_display = None
    
    async def start(self):
        """Start the terminal hub"""
        self.is_running = True
        
        # Configure layout
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        self.layout["left"].split_column(
            Layout(name="batch_info"),
            Layout(name="agent_status")
        )
        
        self.layout["right"].split_column(
            Layout(name="statistics"),
            Layout(name="activity_log")
        )
        
        # Start live display
        self.live_display = Live(
            self.layout,
            console=self.console,
            refresh_per_second=1.0,
            auto_refresh=True
        )
        
        self.live_display.start()
        
        # Initial render
        await self._render_all()
    
    async def stop(self):
        """Stop the terminal hub"""
        self.is_running = False
        if self.live_display:
            self.live_display.stop()
    
    async def update_batch_info(self, batch_number: int, status: str):
        """Update batch information"""
        self.current_batch = batch_number
        self.batch_status = status
        await self._render_batch_info()
    
    async def update_agent_status(self, agent: str, status: str, progress: int = 0, results: int = 0):
        """Update agent status"""
        self.agent_status[agent] = {
            "status": status,
            "progress": progress,
            "results": results
        }
        await self._render_agent_status()
    
    async def update_statistics(self, total_resources: int, total_duplicates: int, current_batch: int):
        """Update system statistics"""
        self.statistics.update({
            "total_resources": total_resources,
            "total_duplicates": total_duplicates,
            "current_batch": current_batch
        })
        await self._render_statistics()
    
    async def log_activity(self, message: str):
        """Log activity message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{timestamp}] {message}")
        
        # Keep only last 20 entries
        if len(self.activity_log) > 20:
            self.activity_log = self.activity_log[-20:]
        
        await self._render_activity_log()
    
    async def log_error(self, message: str):
        """Log error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.error_log.append(f"[{timestamp}] ERROR: {message}")
        
        # Keep only last 10 entries
        if len(self.error_log) > 10:
            self.error_log = self.error_log[-10:]
        
        await self._render_activity_log()
    
    async def _render_all(self):
        """Render all components"""
        await self._render_header()
        await self._render_batch_info()
        await self._render_agent_status()
        await self._render_statistics()
        await self._render_activity_log()
        await self._render_footer()
    
    async def _render_header(self):
        """Render header panel"""
        header_text = Text("🚀 MLIP Curriculum Crowdsourcing System", style="bold blue")
        header_text.append("\nTwo-Agent Architecture: Scraping + Classification", style="dim")
        
        self.layout["header"].update(
            Panel(header_text, style="blue", padding=(1, 2))
        )
    
    async def _render_batch_info(self):
        """Render batch information panel"""
        batch_text = Text(f"Batch #{self.current_batch}", style="bold")
        batch_text.append(f"\nStatus: {self.batch_status}", style="green")
        batch_text.append(f"\nStarted: {datetime.now().strftime('%H:%M:%S')}", style="dim")
        
        self.layout["batch_info"].update(
            Panel(batch_text, title="Current Batch", style="green")
        )
    
    async def _render_agent_status(self):
        """Render agent status panel"""
        table = Table(title="Agent Status")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Progress", style="yellow")
        table.add_column("Results", style="magenta")
        
        for agent_name, status_info in self.agent_status.items():
            progress_bar = "█" * (status_info["progress"] // 10) + "░" * (10 - status_info["progress"] // 10)
            table.add_row(
                agent_name.title(),
                status_info["status"],
                f"{progress_bar} {status_info['progress']}%",
                str(status_info["results"])
            )
        
        self.layout["agent_status"].update(Panel(table, style="cyan"))
    
    async def _render_statistics(self):
        """Render statistics panel"""
        stats_text = Text("System Statistics", style="bold")
        stats_text.append(f"\nTotal Resources: {self.statistics['total_resources']}", style="green")
        stats_text.append(f"\nTotal Duplicates: {self.statistics['total_duplicates']}", style="red")
        stats_text.append(f"\nCurrent Batch: {self.statistics['current_batch']}", style="blue")
        stats_text.append(f"\nSuccess Rate: {self.statistics['success_rate']:.1f}%", style="yellow")
        
        self.layout["statistics"].update(
            Panel(stats_text, title="Statistics", style="magenta")
        )
    
    async def _render_activity_log(self):
        """Render activity log panel"""
        log_text = Text("Activity Log", style="bold")
        
        # Add recent activities
        for activity in self.activity_log[-10:]:
            log_text.append(f"\n{activity}", style="white")
        
        # Add recent errors
        if self.error_log:
            log_text.append("\n\nRecent Errors:", style="bold red")
            for error in self.error_log[-5:]:
                log_text.append(f"\n{error}", style="red")
        
        self.layout["activity_log"].update(
            Panel(log_text, title="Activity Log", style="yellow")
        )
    
    async def _render_footer(self):
        """Render footer panel"""
        footer_text = Text("Press Ctrl+C to stop", style="dim")
        footer_text.append(" | ", style="dim")
        footer_text.append("System Running", style="green")
        
        self.layout["footer"].update(
            Panel(footer_text, style="dim", padding=(0, 2))
        )
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            "current_batch": self.current_batch,
            "batch_status": self.batch_status,
            "agent_status": self.agent_status,
            "statistics": self.statistics,
            "recent_activities": self.activity_log[-5:],
            "recent_errors": self.error_log[-3:]
        }

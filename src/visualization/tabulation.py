"""
Rich-based CLI for V2V Simulation
Provides live-updating tables and statistics during simulation execution.
"""

import sys
import os
from collections import deque
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box
import numpy as np

# Add FinalProject to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'FinalProject'))

from src.SimulationEngine.config import CONFIG
from src.SimulationEngine.simulation_engine import SimulationEngine
from src.SimulationEngine.message import BasicSafetyMessage, CollisionWarningMessage


class SimulationDisplay:
    """Manages Rich-based live display of simulation data."""

    def __init__(self, simulation_engine: SimulationEngine, max_messages: int = 25):
        """
        Initialize the simulation display.

        Args:
            simulation_engine: The simulation engine instance to monitor
            max_messages: Maximum number of messages to display in log
        """
        self.engine = simulation_engine
        self.console = Console()
        self.max_messages = max_messages

        # Message log (ring buffer)
        self.message_log = deque(maxlen=max_messages)

        # Display state
        self.start_time = None
        self.last_update_time = 0

        # Register callbacks with simulation engine
        self.engine.message_callbacks.append(self._on_message_received)

    def _on_message_received(self, vehicle, message):
        """Callback for when simulation generates a message."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if isinstance(message, BasicSafetyMessage):
            msg_type = "BSM"
            color = "cyan"
            details = f"Pos({message.position_x:.1f}, {message.position_y:.1f}) Vel:{message.velocity:.1f}m/s"
            target = "-"
        elif isinstance(message, CollisionWarningMessage):
            msg_type = "CWM"
            color = "red"
            details = f"TTC:{message.time_to_collision:.2f}s {message.warning_type}"
            target = message.target_vehicle_id
        else:
            msg_type = "UNK"
            color = "white"
            details = str(message)
            target = "-"

        self.message_log.append({
            'timestamp': timestamp,
            'type': msg_type,
            'sender': message.vehicle_id,
            'target': target,
            'details': details,
            'color': color
        })

    def _make_config_table(self) -> Table:
        """Create configuration display table."""
        table = Table(
            title="[bold]Simulation Configuration[/bold]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("Parameter", style="cyan", width=30)
        table.add_column("Value", style="yellow", width=20)
        table.add_column("Parameter", style="cyan", width=30)
        table.add_column("Value", style="yellow", width=20)

        # Add config rows (2 columns for compact display)
        table.add_row(
            "Communication Range", f"{CONFIG.COMMUNICATION_RANGE}m",
            "BSM Interval", f"{CONFIG.BSM_INTERVAL}s"
        )
        table.add_row(
            "Highway Speed", f"{CONFIG.HIGHWAY_SPEED:.1f}m/s",
            "City Speed", f"{CONFIG.CITY_SPEED:.1f}m/s"
        )
        table.add_row(
            "Collision Time Threshold", f"{CONFIG.COLLISION_TIME_THRESHOLD}s",
            "Max Deceleration", f"{CONFIG.MAX_DECELERATION}m/s²"
        )
        table.add_row(
            "Simulation Timestep", f"{CONFIG.SIMULATION_TIMESTEP}s",
            "Vehicle Length", f"{CONFIG.VEHICLE_LENGTH}m"
        )

        return table

    def _make_vehicle_table(self) -> Table:
        """Create live vehicle state table."""
        table = Table(
            title="[bold]Vehicle States[/bold]",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold green"
        )

        table.add_column("ID", style="cyan", width=6)
        table.add_column("Position (x, y)", style="white", width=20)
        table.add_column("Velocity", style="yellow", width=12)
        table.add_column("Accel", style="blue", width=10)
        table.add_column("Target", style="magenta", width=10)
        table.add_column("E-Brake", style="red", width=8)

        # Get vehicle states
        vehicles = self.engine.vehicle_manager.get_all_vehicles()

        # Limit display to prevent overflow (show first 15 vehicles)
        display_vehicles = vehicles[:15]

        for vehicle in display_vehicles:
            state = vehicle.get_state_dict()

            # Format emergency brake status
            e_brake = "🚨 YES" if vehicle.emergency_braking else "No"
            e_brake_style = "bold red" if vehicle.emergency_braking else "green"

            table.add_row(
                state['id'],
                state['position'],
                f"{state['velocity']} m/s",
                f"{state['acceleration']} m/s²",
                f"{state['target_vel']} m/s",
                Text(e_brake, style=e_brake_style)
            )

        # Add footer if there are more vehicles
        if len(vehicles) > 15:
            table.caption = f"[dim]Showing 15 of {len(vehicles)} vehicles[/dim]"

        return table

    def _make_statistics_panel(self) -> Panel:
        """Create statistics panel."""
        stats = self.engine.get_simulation_stats()

        # Calculate additional metrics
        elapsed_real = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        speed_ratio = stats['simulation_time'] / elapsed_real if elapsed_real > 0 else 0

        # Build statistics text
        stats_text = Text()
        stats_text.append("⏱️  Simulation Time: ", style="bold cyan")
        stats_text.append(f"{stats['simulation_time']:.2f}s\n", style="yellow")

        stats_text.append("🚗 Total Vehicles: ", style="bold cyan")
        stats_text.append(f"{stats['vehicle_count']}\n", style="yellow")

        stats_text.append("📡 Total BSMs: ", style="bold cyan")
        stats_text.append(f"{stats['total_bsm_sent']} ", style="yellow")
        stats_text.append(f"({stats['bsm_rate']:.1f}/s)\n", style="dim yellow")

        stats_text.append("⚠️  Total CWMs: ", style="bold cyan")
        stats_text.append(f"{stats['total_cwm_sent']}\n", style="red bold")

        stats_text.append("🛡️  Collisions Prevented: ", style="bold cyan")
        stats_text.append(f"{stats['collisions_prevented']}\n", style="green bold")

        stats_text.append("⚡ Speed Ratio: ", style="bold cyan")
        stats_text.append(f"{speed_ratio:.1f}x real-time\n", style="magenta")

        stats_text.append("⏱️  Average Latency: ", style="bold cyan")
        stats_text.append(f"{stats['average_latency']:.7f}s\n", style="yellow")

        stats_text.append("📉  Packet Loss: ", style="bold cyan")
        stats_text.append(f"{(stats['packet_loss'] * 100):.2f}%\n", style="red")

        return Panel(
            stats_text,
            title="[bold]Live Statistics[/bold]",
            border_style="green",
            box=box.ROUNDED
        )

    def _make_message_log_table(self) -> Table:
        """Create message log table."""
        table = Table(
            title="[bold]Message Log[/bold]",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold blue"
        )

        table.add_column("Time", style="dim", width=12)
        table.add_column("Type", width=6)
        table.add_column("Sender", style="cyan", width=8)
        table.add_column("Target", style="magenta", width=8)
        table.add_column("Details", width=50)

        # Display messages in reverse order (newest first)
        for msg in reversed(self.message_log):
            table.add_row(
                msg['timestamp'],
                Text(msg['type'], style=msg['color']),
                msg['sender'],
                msg['target'],
                msg['details']
            )

        if len(self.message_log) == 0:
            table.add_row("-", "-", "-", "-", "[dim]No messages yet[/dim]")

        return table

    def _make_connectivity_matrix(self) -> Table:
        """Create network connectivity matrix showing which vehicles can communicate."""
        table = Table(
            title="[bold]Network Connectivity Matrix[/bold]",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold green"
        )
        
        table.add_column("Vehicle", style="cyan", width=8)
        table.add_column("Connected To", style="green", width=35)
        table.add_column("Count", style="yellow", width=6, justify="right")
        
        # Get all vehicles
        vehicles = self.engine.vehicle_manager.get_all_vehicles()
        
        # Limit to first 10 vehicles for display
        display_vehicles = vehicles[:10]
        
        for vehicle in display_vehicles:
            connected_ids = []
            
            # Check distance to all other vehicles
            for other in vehicles:
                if other. vehicle_id == vehicle.vehicle_id:
                    continue  # Skip self
                
                # Calculate distance using numpy (vehicles have numpy position arrays)
                import numpy as np
                distance = np.linalg.norm(vehicle.position - other.position)
                
                # Check if within communication range (300m)
                if distance <= CONFIG.COMMUNICATION_RANGE:
                    connected_ids.append(other.vehicle_id)
            
            # Format the connected vehicles list
            if connected_ids:
                connected_str = ", ".join(connected_ids[:6])  # Show first 6
                if len(connected_ids) > 6:
                    connected_str += "..."
            else:
                connected_str = "[dim]None[/dim]"
            
            # Add row to table
            table.add_row(
                vehicle.vehicle_id,
                connected_str,
                str(len(connected_ids))
            )
        
        # Add caption if there are more vehicles
        if len(vehicles) > 10:
            table.caption = f"[dim]Showing 10 of {len(vehicles)} vehicles[/dim]"
        
        return table
    

    def _make_layout(self) -> Layout:
        """Create the overall layout combining all display components."""
        layout = Layout()

        # Split into header and body
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )

        # Header
        layout["header"].update(
            Panel(
                "[bold cyan]V2V Network Simulator - Live Display[/bold cyan]",
                style="white on blue"
            )
        )

        # Body split into left and right
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )

        # Left side: vehicles and messages
        layout["left"].split_column(
            Layout(name="vehicles"),
            Layout(name="connectivity"),
            Layout(name="messages")
        )

        # Right side: stats and config
        layout["right"].split_column(
            Layout(name="stats", size=15),
            Layout(name="config")
        )

        return layout

    def generate_display(self) -> Layout:
        """Generate the current display layout with all components."""
        layout = self._make_layout()

        # Update each section
        layout["vehicles"].update(self._make_vehicle_table())
        layout["connectivity"].update(self._make_connectivity_matrix())
        layout["messages"].update(self._make_message_log_table())
        layout["stats"].update(self._make_statistics_panel())
        layout["config"].update(self._make_config_table())

        return layout

    def run_with_live_display(self, duration: float, update_interval: float = 0.1):
        """
        Run simulation with live-updating Rich display.

        Args:
            duration: Simulation duration in seconds
            update_interval: How often to refresh display (in real seconds)
        """
        import time
        import threading

        self.start_time = datetime.now()

        # Flag to control simulation
        self.running = True

        def run_simulation():
            """Run simulation in background thread."""
            try:
                self.engine.run(duration)
            except KeyboardInterrupt:
                pass
            finally:
                self.running = False

        # Start simulation in background thread
        sim_thread = threading.Thread(target=run_simulation, daemon=True)
        sim_thread.start()

        # Live display loop
        try:
            with Live(self.generate_display(), console=self.console, refresh_per_second=10) as live:
                while self.running or sim_thread.is_alive():
                    time.sleep(update_interval)
                    live.update(self.generate_display())

                # Final update after simulation completes
                time.sleep(0.5)
                live.update(self.generate_display())

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Simulation interrupted by user[/yellow]")
            self.running = False

        # Wait for simulation thread to finish
        sim_thread.join(timeout=1.0)

        # Display final summary
        self._display_final_summary()

    def _display_final_summary(self):
        """Display final summary after simulation completes."""
        self.console.print("\n" + "="*80)
        self.console.print("[bold green]✅ Simulation Complete[/bold green]")
        self.console.print("="*80 + "\n")

        stats = self.engine.get_simulation_stats()

        summary_table = Table(box=box.DOUBLE, show_header=False)
        summary_table.add_column("Metric", style="bold cyan", width=40)
        summary_table.add_column("Value", style="bold yellow", width=30)

        summary_table.add_row("Total Simulation Time", f"{stats['simulation_time']:.2f} seconds")
        summary_table.add_row("Total Vehicles Simulated", str(stats['vehicle_count']))
        summary_table.add_row("Total BSM Messages Sent", f"{stats['total_bsm_sent']} ({stats['bsm_rate']:.1f}/s)")
        summary_table.add_row("Total CWM Messages Sent", str(stats['total_cwm_sent']))
        summary_table.add_row("Collisions Prevented", str(stats['collisions_prevented']))

        self.console.print(summary_table)
        self.console.print()



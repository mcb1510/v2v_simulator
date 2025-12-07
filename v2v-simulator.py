#!/usr/bin/env python3
"""
V2V Network Simulator - CLI Entry Point
Rich-based visual interface for running V2V simulations.

Usage:
    python v2v-simulator.py --duration 30 --vehicles 10
    python v2v-simulator.py -d 60 -v 20
"""

import sys
import click
from pathlib import Path

from src.visualization import bootstrap

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.SimulationEngine.config import CONFIG
from src.SimulationEngine.simulation_engine import SimulationEngine
from src.visualization.tabulation import SimulationDisplay
from src.visualization.output import save_statistics


@click.command()
@click.option(
    '-d', '--duration',
    type=float,
    default=30.0,
    show_default=True,
    help='Simulation duration in seconds'
)
@click.option(
    '-v', '--vehicles',
    type=click.IntRange(min=1, max=100),
    default=10,
    show_default=True,
    help='Number of vehicles to spawn'
)
@click.option(
    '--output',
    type=click.Path(),
    help='Save final statistics to file (JSON format)'
)
@click.option(
    '--max-messages',
    type=int,
    default=25,
    show_default=True,
    help='Maximum messages to display in log'
)
def main(duration, vehicles, output, max_messages):
    """
    V2V Network Simulator with Rich visual CLI.

    \b
    Examples:
      python v2v-simulator.py                           # Run with defaults (30s, 10 vehicles)
      python v2v-simulator.py -d 60 -v 20               # Run for 60s with 20 vehicles
      python v2v-simulator.py --duration 45 --vehicles 15

    \b
    Controls:
      Ctrl+C to stop simulation early
    """
    # Validate duration
    if duration <= 0:
        click.secho("❌ Error: Duration must be positive", fg='red', err=True)
        sys.exit(1)

    # Warn for large simulations
    if vehicles > 50:
        click.secho("⚠️  Warning: Large number of vehicles may impact performance", fg='yellow')

    try:
        # Create simulation engine
        simulation_engine = SimulationEngine()
        simulation_engine.initialize()

        # Spawn vehicles
        click.echo(f"🚗 Spawning {vehicles} vehicles...")
        bootstrap.spawn_vehicles(simulation_engine, vehicles)

        # Create display
        display = SimulationDisplay(
            simulation_engine,
            max_messages=max_messages
        )

        # Run simulation with live display
        click.echo(f"▶️  Starting simulation for {duration}s...\n")
        display.run_with_live_display(duration=duration)

        # Save output if requested
        if output:
            stats = simulation_engine.get_simulation_stats()
            save_statistics(stats, output)

    except KeyboardInterrupt:
        click.secho("\n⚠️  Simulation interrupted by user", fg='yellow')
        sys.exit(0)

    except Exception as e:
        click.secho(f"\n❌ Error: {e}", fg='red', err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

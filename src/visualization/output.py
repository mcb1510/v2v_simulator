"""
Functions to save visualization outputs and statistics.
"""

def save_statistics(stats: dict, output_file: str):
    """Save final statistics to JSON file."""
    import json
    from datetime import datetime

    # Add metadata
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'statistics': stats
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"📊 Statistics saved to: {output_file}")

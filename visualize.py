import os
import re
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from matplotlib.gridspec import GridSpec

def parse_log_file(log_path):
    """Parse a machine log file into a structured DataFrame."""
    events = []

    with open(log_path, 'r') as f:
        for line in f:
            # Parse the log line format: [event]: system_time logical_clock extra_text
            match = re.match(r'\[(.+)\]: ([0-9:.]+) ([0-9:.]+) (.*)', line)
            if match:
                event_type, system_time, logical_clock, extra_text = match.groups()

                # Convert system_time to datetime object
                system_time = datetime.strptime(system_time, '%H:%M:%S.%f')

                logical_time = datetime.strptime(logical_clock, '%H:%M:%S.%f')

                # Parse extra text for message destinations (A, B, AB)
                destinations = extra_text.strip()

                events.append({
                    'event_type': event_type,
                    'system_time': system_time,
                    'logical_clock': logical_time,
                    'destinations': destinations,
                    'queue_size': int(destinations.split(': ')[1]) if 'Queued Messages' in destinations else 0
                })

    return pd.DataFrame(events)

def parse_parameters(param_path):
    """Parse experiment parameters file."""
    params = {}
    with open(param_path, 'r') as f:
        for line in f:
            if ':' in line:
                key, value = line.split(':', 1)
                params[key.strip()] = value.strip()
    return params

def analyze_experiment(experiment_dir):
    """Analyze a single experiment directory."""
    # Get parameters
    param_path = os.path.join(experiment_dir, 'parameters.txt')
    if not os.path.exists(param_path):
        print(f"Parameters file not found in {experiment_dir}")
        return None

    params = parse_parameters(param_path)

    # Get machine logs
    machine_logs = {}
    for log_file in glob.glob(os.path.join(experiment_dir, 'machine_*.log')):
        machine_id = int(re.search(r'machine_(\d+)\.log', log_file).group(1))
        machine_logs[machine_id] = parse_log_file(log_file)

    if not machine_logs:
        print(f"No log files found in {experiment_dir}")
        return None

    # Add machine_id to each DataFrame
    for machine_id, df in machine_logs.items():
        df['machine_id'] = machine_id

    # Combine all logs
    all_logs = pd.concat(machine_logs.values())

    # Add experiment info
    all_logs['experiment'] = os.path.basename(experiment_dir)
    all_logs['clock_variation'] = params.get('Clock variation', 'unknown')
    all_logs['internal_event_prob'] = params.get('Internal event probability', 'unknown')
    all_logs['duration'] = params.get('Duration', 'unknown')

    # Extract machine speeds if available
    if 'Machine speeds' in params:
        speeds_str = params['Machine speeds']
        speeds = eval(speeds_str)  # Convert string representation of list to actual list
        all_logs['machine_speed'] = all_logs['machine_id'].map(lambda x: speeds[x] if x < len(speeds) else None)

    return all_logs

def visualize_experiment(experiment_data, output_dir=None):
    """Create consolidated visualizations for an experiment."""
    if experiment_data is None or experiment_data.empty:
        print("No data to visualize")
        return

    experiment_name = experiment_data['experiment'].iloc[0]

    # Create output directory if needed
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base_path = os.path.join(output_dir, experiment_name)
    else:
        base_path = experiment_name

    # Create a consolidated figure with multiple subplots
    fig = plt.figure(figsize=(20, 15))
    gs = GridSpec(3, 2, figure=fig)

    # 1. Logical Clock Progression (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    for machine_id in experiment_data['machine_id'].unique():
        machine_data = experiment_data[experiment_data['machine_id'] == machine_id]
        ax1.plot(machine_data['system_time'], machine_data['logical_clock'],
                label=f'Machine {machine_id} (Speed: {machine_data["machine_speed"].iloc[0]})')

    ax1.set_xlabel('System Time')
    ax1.set_ylabel('Logical Clock Value')
    ax1.set_title('Logical Clock Progression')
    ax1.legend()
    ax1.grid(True)

    # 2. Event Type Distribution (top right)
    ax2 = fig.add_subplot(gs[0, 1])
    event_counts = experiment_data.groupby(['machine_id', 'event_type']).size().unstack()
    event_counts.plot(kind='bar', ax=ax2)
    ax2.set_xlabel('Machine ID')
    ax2.set_ylabel('Event Count')
    ax2.set_title('Event Type Distribution')
    ax2.legend(title='Event Type')

    # 3. Message Queue Size Over Time (middle left)
    ax3 = fig.add_subplot(gs[1, 0])
    for machine_id in experiment_data['machine_id'].unique():
        machine_data = experiment_data[experiment_data['machine_id'] == machine_id]
        recv_events = machine_data[machine_data['event_type'] == 'recv']
        if not recv_events.empty:
            ax3.plot(recv_events['system_time'], recv_events['queue_size'],
                    label=f'Machine {machine_id}', marker='o')

    ax3.set_xlabel('System Time')
    ax3.set_ylabel('Queue Size')
    ax3.set_title('Message Queue Size')
    ax3.legend()
    ax3.grid(True)

    # 4. Clock Drift Analysis (middle right)
    ax4 = fig.add_subplot(gs[1, 1])

    # Calculate clock drift (difference between logical clock and expected progression)
    for machine_id in experiment_data['machine_id'].unique():
        machine_data = experiment_data[experiment_data['machine_id'] == machine_id].copy()
        machine_data = machine_data.sort_values('system_time')

        # Calculate drift
        machine_data['clock_drift'] = (machine_data['logical_clock'] - machine_data['system_time']).dt.total_seconds()

        ax4.plot(machine_data['system_time'], machine_data['clock_drift'],
                label=f'Machine {machine_id} (Speed: {machine_data["machine_speed"].iloc[0]})')

    ax4.set_xlabel('System Time')
    ax4.set_ylabel('Clock Drift (seconds)')
    ax4.set_title('Logical Clock Drift')
    ax4.legend()
    ax4.grid(True)

    # 5. Message Sending Patterns (bottom)
    ax5 = fig.add_subplot(gs[2, :])
    send_events = experiment_data[experiment_data['event_type'] == 'send']

    # Count different message destinations
    dest_counts = {
        'A only': send_events[send_events['destinations'] == 'A'].shape[0],
        'B only': send_events[send_events['destinations'] == 'B'].shape[0],
        'Both (AB)': send_events[send_events['destinations'] == 'AB'].shape[0]
    }

    ax5.bar(dest_counts.keys(), dest_counts.values())
    ax5.set_xlabel('Message Destination')
    ax5.set_ylabel('Count')
    ax5.set_title('Message Sending Patterns')

    # Add experiment parameters as a title
    clock_var = experiment_data['clock_variation'].iloc[0]
    event_prob = experiment_data['internal_event_prob'].iloc[0]
    duration = experiment_data['duration'].iloc[0]
    speeds = experiment_data.groupby('machine_id')['machine_speed'].first().tolist()

    fig.suptitle(f"Experiment: {experiment_name}\n"
                f"Clock Variation: {clock_var}, Event Probability: {event_prob}, Duration: {duration}s\n"
                f"Machine Speeds: {speeds}", fontsize=16)

    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for the suptitle
    plt.savefig(f'{base_path}_analysis.png')
    plt.close(fig)

    print(f"Consolidated visualization created for {experiment_name}")

def compare_experiments(experiment_dirs, output_dir="experiment_comparison"):
    """Compare multiple experiments in a single consolidated visualization."""
    all_data = []

    for exp_dir in experiment_dirs:
        data = analyze_experiment(exp_dir)
        if data is not None:
            all_data.append(data)

    if not all_data:
        print("No valid experiment data to compare")
        return

    combined_data = pd.concat(all_data)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create a consolidated comparison figure
    fig = plt.figure(figsize=(20, 15))
    gs = GridSpec(2, 2, figure=fig)

    # 1. Compare logical clock progression rates (top left)
    ax1 = fig.add_subplot(gs[0, 0])

    exp_data = []
    labels = []

    for exp in combined_data['experiment'].unique():
        exp_subset = combined_data[combined_data['experiment'] == exp]

        # Get the max logical clock value for each experiment
        max_clock = exp_subset.groupby('machine_id')['logical_clock'].max().mean()

        # Get experiment parameters for the label
        clock_var = exp_subset['clock_variation'].iloc[0]
        event_prob = exp_subset['internal_event_prob'].iloc[0]

        exp_data.append(max_clock)
        labels.append(f"{exp}\n{clock_var}/{event_prob}")

    ax1.bar(labels, exp_data)
    ax1.set_xlabel('Experiment')
    ax1.set_ylabel('Average Max Logical Clock')
    ax1.set_title('Comparison of Logical Clock Progression Rates')
    ax1.tick_params(axis='x', rotation=45)

    # 2. Compare event type distributions (top right)
    ax2 = fig.add_subplot(gs[0, 1])

    event_counts = combined_data.groupby(['experiment', 'event_type']).size().unstack()
    event_counts.plot(kind='bar', ax=ax2)

    ax2.set_xlabel('Experiment')
    ax2.set_ylabel('Event Count')
    ax2.set_title('Comparison of Event Type Distributions')
    ax2.legend(title='Event Type')
    ax2.tick_params(axis='x', rotation=45)

    # 3. Compare queue sizes (bottom left)
    ax3 = fig.add_subplot(gs[1, 0])

    queue_stats = combined_data[combined_data['event_type'] == 'recv'].groupby('experiment')['queue_size'].agg(['mean', 'max'])

    width = 0.35
    x = np.arange(len(queue_stats.index))

    ax3.bar(x - width/2, queue_stats['mean'], width, label='Mean Queue Size')
    ax3.bar(x + width/2, queue_stats['max'], width, label='Max Queue Size')

    ax3.set_xlabel('Experiment')
    ax3.set_ylabel('Queue Size')
    ax3.set_title('Comparison of Message Queue Sizes')
    ax3.set_xticks(x)
    ax3.set_xticklabels(queue_stats.index, rotation=45)
    ax3.legend()

    # 4. Compare clock drift (bottom right)
    ax4 = fig.add_subplot(gs[1, 1])

    for exp in combined_data['experiment'].unique():
        exp_subset = combined_data[combined_data['experiment'] == exp]

        # Calculate average clock drift for each experiment
        drift_data = []
        for machine_id in exp_subset['machine_id'].unique():
            machine_data = exp_subset[exp_subset['machine_id'] == machine_id].copy()
            machine_data = machine_data.sort_values('system_time')

            # Calculate drift
            machine_data['clock_drift'] = (machine_data['logical_clock'] - machine_data['system_time']).dt.total_seconds()

            # Get final drift
            final_drift = machine_data['clock_drift'].iloc[-1]
            drift_data.append(final_drift)

        # Get experiment parameters for the label
        clock_var = exp_subset['clock_variation'].iloc[0]
        event_prob = exp_subset['internal_event_prob'].iloc[0]

        ax4.bar(f"{exp}\n{clock_var}/{event_prob}", np.mean(drift_data))

    ax4.set_xlabel('Experiment')
    ax4.set_ylabel('Average Final Clock Drift (seconds)')
    ax4.set_title('Comparison of Final Clock Drift')
    ax4.tick_params(axis='x', rotation=45)

    fig.suptitle("Experiment Comparison", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for the suptitle
    plt.savefig(f'{output_dir}/experiment_comparison.png')
    plt.close(fig)

    print(f"Consolidated comparison visualization created in {output_dir}")

def main():
    """Main function to find and visualize experiments."""
    # Find all experiment directories
    experiment_dirs = [d for d in glob.glob("experiment_*") if os.path.isdir(d)]

    if not experiment_dirs:
        print("No experiment directories found")
        return

    print(f"Found {len(experiment_dirs)} experiment directories")

    # Create output directory for visualizations
    output_dir = "experiment_visualizations"
    os.makedirs(output_dir, exist_ok=True)

    # Analyze and visualize each experiment
    for exp_dir in experiment_dirs:
        print(f"Analyzing {exp_dir}...")
        exp_data = analyze_experiment(exp_dir)
        if exp_data is not None:
            visualize_experiment(exp_data, output_dir)

    # Compare experiments
    compare_experiments(experiment_dirs)

if __name__ == "__main__":
    main()

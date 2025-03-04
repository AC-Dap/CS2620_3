import matplotlib.pyplot as plt
import pandas as pd
import re
import glob
import os

def parse_log_file(file_path):
    """Parse a log file and extract timestamps and logical clock values."""
    data = []
    machine_id = os.path.basename(file_path).split('.')[0]
    
    with open(file_path, 'r') as f:
        for line in f:
            # Extract event type, system time, and logical clock
            match = re.match(r'\[(.*?)\]: (.*?) (\d+)(.*)', line)
            if match:
                event_type = match.group(1)
                system_time = match.group(2)
                logical_clock = int(match.group(3))
                extra_info = match.group(4).strip()
                
                # Convert system time to seconds since start
                time_parts = system_time.split(':')
                seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + float(time_parts[2])
                
                data.append({
                    'machine': machine_id,
                    'event': event_type,
                    'system_time': seconds,
                    'logical_clock': logical_clock,
                    'extra_info': extra_info
                })
    
    return pd.DataFrame(data)

def visualize_experiment(experiment_dir):
    """Visualize the results of an experiment."""
    log_files = glob.glob(f"{experiment_dir}/*.log")
    
    if not log_files:
        print(f"No log files found in {experiment_dir}")
        return
    
    # Parse all log files
    all_data = pd.concat([parse_log_file(file) for file in log_files])
    
    # Normalize system time to start at 0
    min_time = all_data['system_time'].min()
    all_data['system_time'] = all_data['system_time'] - min_time
    
    # Create plots
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Logical clock values over time for each machine
    plt.subplot(2, 2, 1)
    for machine, group in all_data.groupby('machine'):
        plt.plot(group['system_time'], group['logical_clock'], label=f'Machine {machine}')
    plt.xlabel('System Time (seconds)')
    plt.ylabel('Logical Clock Value')
    plt.title('Logical Clock Progression')
    plt.legend()
    plt.grid(True)
    
    # Plot 2: Clock drift (difference between machines)
    plt.subplot(2, 2, 2)
    machines = all_data['machine'].unique()
    for i in range(len(machines)):
        for j in range(i+1, len(machines)):
            machine1 = machines[i]
            machine2 = machines[j]
            
            # Merge data from both machines
            m1_data = all_data[all_data['machine'] == machine1][['system_time', 'logical_clock']]
            m2_data = all_data[all_data['machine'] == machine2][['system_time', 'logical_clock']]
            
            # Resample to common time points
            combined = pd.merge_asof(
                m1_data.sort_values('system_time'), 
                m2_data.sort_values('system_time'),
                on='system_time', 
                direction='nearest',
                suffixes=('_1', '_2')
            )
            
            # Calculate drift
            combined['drift'] = combined['logical_clock_1'] - combined['logical_clock_2']
            plt.plot(combined['system_time'], combined['drift'], label=f'{machine1} - {machine2}')
    
    plt.xlabel('System Time (seconds)')
    plt.ylabel('Clock Drift')
    plt.title('Logical Clock Drift Between Machines')
    plt.legend()
    plt.grid(True)
    
    # Plot 3: Message queue lengths
    plt.subplot(2, 2, 3)
    recv_data = all_data[all_data['event'] == 'recv']
    for machine, group in recv_data.groupby('machine'):
        # Extract queue size from extra_info
        queue_sizes = []
        times = []
        for _, row in group.iterrows():
            match = re.search(r'Queued Messages: (\d+)', row['extra_info'])
            if match:
                queue_sizes.append(int(match.group(1)))
                times.append(row['system_time'])
        
        plt.plot(times, queue_sizes, label=f'Machine {machine}')
    
    plt.xlabel('System Time (seconds)')
    plt.ylabel('Queue Length')
    plt.title('Message Queue Lengths')
    plt.legend()
    plt.grid(True)
    
    # Plot 4: Event distribution
    plt.subplot(2, 2, 4)
    event_counts = all_data.groupby(['machine', 'event']).size().unstack()
    event_counts.plot(kind='bar')
    plt.xlabel('Machine')
    plt.ylabel('Event Count')
    plt.title('Distribution of Events')
    plt.legend(title='Event Type')
    
    plt.tight_layout()
    plt.savefig(f"{experiment_dir}/visualization.png")
    plt.close()
    
    print(f"Visualization saved to {experiment_dir}/visualization.png")

def main():
    # Find all experiment directories
    experiment_dirs = [d for d in glob.glob("experiment_*") if os.path.isdir(d)]
    
    if not experiment_dirs:
        print("No experiment directories found. Please run experiments first.")
        return
    
    for exp_dir in experiment_dirs:
        print(f"Visualizing results for {exp_dir}...")
        visualize_experiment(exp_dir)

if __name__ == "__main__":
    main() 
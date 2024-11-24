import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas import DataFrame, json_normalize, concat
from pathlib import Path


def plot_usage_data(df: DataFrame, store_as: Path):
    """Frame and plot CPU and RAM usage"""
    # Frame
    group_cols = ['hour']
    usage = df[group_cols + ['cpu', 'ram']].groupby(group_cols).agg(
        cpu=('cpu', 'mean'),
        ram=('ram', 'mean'),
    ).reset_index()

    # Plot
    plt.figure(figsize=(7, 3))

    plt.plot(usage['hour'], usage['cpu'], color='orange', label='CPU', linewidth=2)
    plt.plot(usage['hour'], usage['ram'], color='green', label='Memory', linewidth=2)

    plt.ylim(0, 100)
    plt.yticks(range(0, 101, 10))

    plt.ylabel('Percentage Usage (%)')
    plt.title('CPU and RAM Usage')
    plt.legend(loc='upper left')

    plt.yticks(range(0, 101, 20))  # Set Y-axis ticks at intervals of 20
    plt.grid(axis='y', linestyle=':', color='gray', linewidth=0.5)

    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))  # Major ticks every 6 hours
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%a, %H:%M"))
    plt.xticks(rotation=30, fontsize=7, ha='right')

    plt.tight_layout()
    plt.savefig(store_as)
    plt.close()

    print(f'Usage plot stored at {store_as}')


def plot_net_data(df: DataFrame, network_device: str, store_as: Path):
    """Frame and plot networking data"""
    # Transform
    net = json_normalize(df['net'], sep='_').fillna(0)
    net.reset_index(drop=True, inplace=True)
    net.rename(
        columns={
            f'{network_device}_in': 'rate_in',
            f'{network_device}_out': 'rate_out',
        }, inplace=True,
    )
    df = concat([df.drop(columns=['net']), net], axis=1)

    # Frame
    group_cols = ['hour']
    data_cols = ['rate_in', 'rate_out']
    net = df[group_cols + data_cols].groupby(group_cols).agg(
        rate_in=('rate_in', 'mean'),
        rate_out=('rate_out', 'mean'),
    )
    net['stacked'] = net['rate_in'] + net['rate_out']
    net.reset_index(inplace=True)

    # Plot
    plt.figure(figsize=(9, 5))

    plt.fill_between(net['hour'], 0, net['rate_in'], label='Inbound', color='blue', alpha=0.7)
    plt.fill_between(net['hour'], net['rate_in'], net['stacked'], label='Outbound', color='red', alpha=0.7)

    plt.title("Network Activity")
    plt.xlabel("Time")
    plt.ylabel("Rate (bytes/min)")
    plt.legend()

    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))  # Major ticks every 6 hours
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%a, %H:%M"))
    plt.xticks(rotation=45, fontsize=9, ha='right')

    plt.ylim(0, net[['rate_in', 'rate_out']].quantile(0.99).max())

    plt.tight_layout()
    plt.savefig(store_as)
    plt.close()

    print(f'Networking plot stored at {store_as}')

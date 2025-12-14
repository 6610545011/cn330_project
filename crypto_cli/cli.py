import click
from .utils import get_crypto_price, calculate_sma, calculate_rsi, get_ticker # Import เพิ่ม

@click.group()
def cli():
    """Crypto CLI Tool"""
    pass

# --- คำสั่งเดิม (ย้ายมาอยู่ใต้ cli) ---
@cli.command()
@click.argument("coin")
def price(coin):
    """Get the current price."""
    data = get_crypto_price(coin)
    if "error" in data:
        click.secho(f"Error: {data['error']}", fg="red")
    else:
        click.echo(f"{data['name']}: ${data['price']:,.4f}")

@cli.command()
@click.argument("coin")
@click.argument("timestamps", nargs=-1)
def changes(coin, timestamps):
    """Get percentage price changes for specific timestamps."""
    data = get_ticker(coin)
    if "error" in data:
        click.secho(f"Error: {data['error']}", fg="red")
        return

    name = data.get("name")
    symbol = data.get("symbol")
    quotes = data.get("quotes", {}).get("USD", {})

    click.secho(f"📊 Price changes for {name} ({symbol})", bold=True)

    if not timestamps:
        # If no timestamps provided, show all available in a logical order
        preferred_order = ["15m", "30m", "1h", "6h", "12h", "24h", "7d", "30d", "1y"]
        timestamps = []
        for ts in preferred_order:
            if f"percent_change_{ts}" in quotes:
                timestamps.append(ts)
        # Add any others found in the response
        for key in quotes:
            if key.startswith("percent_change_") and key.replace("percent_change_", "") not in timestamps:
                timestamps.append(key.replace("percent_change_", ""))

    for ts in timestamps:
        key = f"percent_change_{ts.lower()}"
        val = quotes.get(key)
        if val is not None:
            color = "green" if val > 0 else ("red" if val < 0 else "white")
            sign = "+" if val > 0 else ""
            click.secho(f"{ts+':':<5} {sign}{val}%", fg=color)
        else:
            click.secho(f"{ts+':':<5} N/A", fg="yellow")

# --- คำสั่งใหม่: Analyze Group ---
@cli.group()
def analyze():
    """Technical Analysis tools."""
    pass

@analyze.command()
@click.argument("coin")
@click.option("--period", default=14, help="Period for SMA (default 14)")
def sma(coin, period):
    """Calculate Simple Moving Average."""
    # ลบ click.echo บรรทัดนี้ออก หรือเปลี่ยนเป็นข้อความรอ
    click.echo(f"Fetching data for '{coin}'...") 

    data = calculate_sma(coin, window=period)
    
    if "error" in data:
        click.secho(f"Error: {data['error']}", fg="red")
    else:
        # --- Print ชื่อจริงตรงนี้ ---
        click.secho(f"\n=== Analysis for {data['coin_name']} ({data['coin_symbol']}) ===", fg="cyan", bold=True)
        
        click.secho(f"SMA ({data['period']}): ${data['value']:,.2f}", fg="yellow")
        click.secho(f"Current Price: ${data['current_price']:,.2f}", fg="white")
        
        color = "green" if "BUY" in data['signal'] else "red"
        click.secho(f"Signal: {data['signal']}", fg=color, bold=True)

@analyze.command()
@click.argument("coin")
def rsi(coin):
    """Calculate RSI (Relative Strength Index)."""
    # ลบ click.echo บรรทัดนี้ออก หรือเปลี่ยนเป็นข้อความรอ
    click.echo(f"Fetching data for '{coin}'...")

    data = calculate_rsi(coin)
    
    if "error" in data:
        click.secho(f"Error: {data['error']}", fg="red")
    else:
        # --- Print ชื่อจริงตรงนี้ ---
        click.secho(f"\n=== Analysis for {data['coin_name']} ({data['coin_symbol']}) ===", fg="cyan", bold=True)
        
        click.secho(f"RSI (14): {data['value']:.2f}", fg="yellow")
        
        color = "green" if "BUY" in data['signal'] else ("red" if "SELL" in data['signal'] else "white")
        click.secho(f"Signal: {data['signal']}", fg=color, bold=True)

if __name__ == "__main__":
    cli()
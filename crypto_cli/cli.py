import click
from .utils import get_crypto_price

@click.command()
@click.argument("coin")
def price(coin):
    """Get the price from command line."""
    data = get_crypto_price(coin)
    if "error" in data:
        # Use click's styling for errors
        click.secho(f"Error: {data['error']}", fg="red")
    else:
        # Format the output for better readability
        click.echo(f"{data['name']}: ${data['price']:,.4f}")

if __name__ == "__main__":
    price()

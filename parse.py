import argparse
import json
import os
import re
from datetime import datetime
from typing import Any

from pypdf import PdfReader

from currency_converter import CurrencyConverter

date_regex = re.compile(r"Schlusstag\s*(\d{2}\.\d{2}\.\d{4})")
date_time_regex = re.compile(r"Schlusstag/-Zeit\s*(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})")
isin_regex = re.compile(r"(IE\w{10})")
pieces_regex = re.compile(r"Stück\s*(\d+)(?:,(\d+))?")
price_regex = re.compile(r"Ausführungskurs\s*(\d+),(\d+)\s+EUR")

c = CurrencyConverter()

mapping = {}
with open('mapping.json', 'r') as file:
    mapping = json.load(file)

def generate_dkb_trade_data(input_directory: str, output_file: str, merge: bool) -> None:
    """
    Extracts trade data from DKB PDFs and saves it to a JSON file.
    """
    if merge and os.path.exists(output_file):
        with open(output_file) as f:
            data = json.load(f)
    else:
        data = {
            "activities": [],
        }
    for file in os.listdir(input_directory):
        joined_path = os.path.join(input_directory, file)
        if file.endswith(".pdf"):
            if file.startswith("Kauf_") and "Wertpapierabrechnung" in file:
                trade_type = "BUY"
            elif file.startswith("Verkauf_") and "Wertpapierabrechnung" in file:
                trade_type = "SELL"
            else:
                print(f"Skipping {joined_path}...")
                continue
            print(f"Processing {joined_path}...")
            pdf = PdfReader(joined_path)
            text = pdf.pages[0].extract_text()
            trade = parse_trade_data(text)
            trade["type"] = trade_type
            symbol = mapping[trade["symbol"]]
            trade["symbol"] = symbol
            for existing_trade in data["activities"]:
                if existing_trade["date"] == trade["date"]:
                    print(f"Skipping duplicate trade on {trade['date']} to {symbol}...")
                    break
            else:
                data["activities"].append(trade)
                print(f"Added trade on {trade['date']} to {symbol}")

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def parse_trade_data(text: str) -> dict[str, Any]:
    isin = re.search(isin_regex, text).group(1)
    date_and_time = re.search(date_time_regex, text)
    if date_and_time:
        parsed_datetime = datetime.strptime(date_and_time.group(1), "%d.%m.%Y %H:%M:%S")
    else:
        date = re.search(date_regex, text).group(1)
        parsed_datetime = datetime.strptime(date, "%d.%m.%Y")
    pieces = re.search(pieces_regex, text)
    parsed_pieces = float(pieces.group(1)) + (float(f"0.{pieces.group(2)}") if pieces.group(2) else 0)
    price = re.search(price_regex, text)
    parsed_price = float(price.group(1)) + (float(f"0.{price.group(2)}") if price.group(2) else 0)
    return {
        "accountId": "e2a4628f-1146-4ab8-b559-6058c7657bbb",
        "comment": "",
        "fee": 0,
        "quantity": parsed_pieces,
        "unitPrice": c.convert(parsed_price, 'EUR', 'USD',date=parsed_datetime),
        "currency": "USD",
        "dataSource": "YAHOO",
        "date": parsed_datetime.isoformat(),
        "symbol": isin,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input-directory",
        type=str,
        default="DKB",
        help="Directory containing DKB trade data PDFs",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        default="dkb.json",
        help="Output file for DKB trade data",
    )
    parser.add_argument(
        "-m",
        "--merge",
        action="store_true",
        help="Merge with existing data",
    )
    args = parser.parse_args()
    generate_dkb_trade_data(args.input_directory, args.output_file, args.merge)

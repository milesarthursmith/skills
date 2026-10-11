#!/usr/bin/env python3
"""Draw oblique strategy cards at random.

Usage:
  python3 draw.py                 # one card from the whole deck
  python3 draw.py -n 3            # three different cards
  python3 draw.py -k Perturbation # only from one kind
  python3 draw.py --list-kinds
"""
import argparse, json, random, pathlib

DECK = pathlib.Path(__file__).resolve().parent.parent / "references" / "cards.json"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-n", type=int, default=1, help="number of cards")
    p.add_argument("-k", "--kind", help="limit to one kind (case-insensitive)")
    p.add_argument("--list-kinds", action="store_true")
    a = p.parse_args()

    cards = json.loads(DECK.read_text())
    if a.list_kinds:
        print("\n".join(sorted({c["kind"] for c in cards})))
        return
    if a.kind:
        cards = [c for c in cards if c["kind"].lower() == a.kind.lower()]
        if not cards:
            raise SystemExit(f"No cards of kind '{a.kind}'. Use --list-kinds.")

    for c in random.sample(cards, min(a.n, len(cards))):
        print(f"#{c['id']} [{c['kind']}] {c['card']}\n"
              f"  Source: {c['source']}\n"
              f"  Why: {c['why']}\n"
              f"  Do: {c['prompt']}\n")

if __name__ == "__main__":
    main()

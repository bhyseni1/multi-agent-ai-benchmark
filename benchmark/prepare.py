"""Prepare original open benchmark splits with hashes and exact dataset revision."""
import argparse
from .public_data import SOURCES,prepare_public

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset',choices=SOURCES,default='gsm8k')
    p.add_argument('--limit',type=int,default=100)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--revision',help='Optional immutable HF dataset commit SHA')
    p.add_argument('--out',help='Output CSV path')
    a=p.parse_args()
    print(prepare_public(a.dataset,a.out,a.limit,a.seed,a.revision))

if __name__=='__main__':main()

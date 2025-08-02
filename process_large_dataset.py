#!/usr/bin/env python3
"""
Script to process very large URL datasets in chunks
"""

import os
import sys
from pathlib import Path
from typing import List, Set
import argparse

def split_large_file(input_file: Path, chunk_size: int = 10000) -> List[Path]:
    """Split a large file into smaller chunks"""
    chunk_files = []
    
    with open(input_file, 'r') as f:
        chunk_num = 1
        chunk_lines = []
        
        for line in f:
            chunk_lines.append(line.strip())
            
            if len(chunk_lines) >= chunk_size:
                # Write chunk
                chunk_file = input_file.parent / f"{input_file.stem}_chunk_{chunk_num}.txt"
                with open(chunk_file, 'w') as cf:
                    cf.write('\n'.join(chunk_lines) + '\n')
                chunk_files.append(chunk_file)
                
                # Reset for next chunk
                chunk_lines = []
                chunk_num += 1
        
        # Write remaining lines
        if chunk_lines:
            chunk_file = input_file.parent / f"{input_file.stem}_chunk_{chunk_num}.txt"
            with open(chunk_file, 'w') as cf:
                cf.write('\n'.join(chunk_lines) + '\n')
            chunk_files.append(chunk_file)
    
    return chunk_files

def process_chunks(chunk_files: List[Path], output_file: Path, command: str):
    """Process each chunk and combine results"""
    all_results = set()
    
    for i, chunk_file in enumerate(chunk_files, 1):
        print(f"Processing chunk {i}/{len(chunk_files)}: {chunk_file}")
        
        # Run validation on this chunk
        cmd = f"python -m mjsrecon validation --independent --input {chunk_file} --output ./chunk_output"
        print(f"Running: {cmd}")
        
        # Execute command and capture output
        result = os.system(cmd)
        
        if result == 0:
            # Read results from chunk output
            chunk_results_file = Path("./chunk_output/live_urls.txt")
            if chunk_results_file.exists():
                with open(chunk_results_file, 'r') as f:
                    chunk_results = set(line.strip() for line in f if line.strip())
                all_results.update(chunk_results)
                print(f"Added {len(chunk_results)} live URLs from chunk {i}")
        
        # Clean up chunk output
        if Path("./chunk_output").exists():
            import shutil
            shutil.rmtree("./chunk_output")
    
    # Save combined results
    with open(output_file, 'w') as f:
        for url in sorted(all_results):
            f.write(f"{url}\n")
    
    print(f"Combined results saved to: {output_file}")
    print(f"Total live URLs found: {len(all_results)}")

def main():
    parser = argparse.ArgumentParser(description="Process large URL datasets in chunks")
    parser.add_argument("input_file", type=Path, help="Input file with URLs")
    parser.add_argument("--chunk-size", type=int, default=10000, help="Number of URLs per chunk")
    parser.add_argument("--output", type=Path, default=Path("combined_live_urls.txt"), help="Output file")
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: Input file {args.input_file} not found")
        sys.exit(1)
    
    print(f"Processing large dataset: {args.input_file}")
    print(f"Chunk size: {args.chunk_size}")
    
    # Split the file into chunks
    chunk_files = split_large_file(args.input_file, args.chunk_size)
    print(f"Created {len(chunk_files)} chunks")
    
    # Process each chunk
    process_chunks(chunk_files, args.output, "validation")
    
    # Clean up chunk files
    for chunk_file in chunk_files:
        chunk_file.unlink()
    
    print("Processing complete!")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Script to process very large URL datasets in chunks
"""

import os
import sys
from pathlib import Path
from typing import List, Set
import argparse

# Add the project root to the path to import config
sys.path.insert(0, str(Path(__file__).parent))
from common.config import CONFIG
from common.logger import Logger

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

def process_chunks(chunk_files: List[Path], output_file: Path, command: str, target_output_dir: Path, logger: Logger):
    """Process each chunk and combine results"""
    all_results = set()
    
    for i, chunk_file in enumerate(chunk_files, 1):
        logger.info(f"Processing chunk {i}/{len(chunk_files)}: {chunk_file}")
        
        # Create temporary output directory for this chunk
        chunk_output_dir = target_output_dir / f"chunk_output_{i}"
        chunk_output_dir.mkdir(exist_ok=True)
        
        # Run validation on this chunk using target output directory
        cmd = f"python -m mjsrecon validation --independent --input {chunk_file} --output {target_output_dir}"
        logger.info(f"Running: {cmd}")
        
        # Execute command and capture output
        result = os.system(cmd)
        
        if result == 0:
            # Read results from chunk output using config file path
            live_js_file = target_output_dir / CONFIG['files']['live_js']
            if live_js_file.exists():
                with open(live_js_file, 'r') as f:
                    chunk_results = set(line.strip() for line in f if line.strip())
                all_results.update(chunk_results)
                logger.info(f"Added {len(chunk_results)} live URLs from chunk {i}")
        
        # Clean up chunk output
        if chunk_output_dir.exists():
            import shutil
            shutil.rmtree(chunk_output_dir)
    
    # Save combined results using config
    with open(output_file, 'w') as f:
        for url in sorted(all_results):
            f.write(f"{url}\n")
    
    logger.success(f"Combined results saved to: {output_file}")
    logger.info(f"Total live URLs found: {len(all_results)}")

def main():
    parser = argparse.ArgumentParser(description="Process large URL datasets in chunks")
    parser.add_argument("input_file", type=Path, help="Input file with URLs")
    parser.add_argument("--chunk-size", type=int, default=10000, help="Number of URLs per chunk")
    parser.add_argument("--output", type=Path, help="Output file (optional, will use config default)")
    parser.add_argument("--target-output-dir", type=Path, default=Path("./output"), help="Target output directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress console output except for warnings and errors")
    
    args = parser.parse_args()
    
    # Setup logger
    logger = Logger(log_dir=args.target_output_dir, verbose=args.verbose, quiet=args.quiet)
    
    if not args.input_file.exists():
        logger.error(f"Input file {args.input_file} not found")
        sys.exit(1)
    
    # Use config for output file if not specified
    if not args.output:
        args.output = args.target_output_dir / CONFIG['files']['live_js']
    
    logger.info(f"Processing large dataset: {args.input_file}")
    logger.info(f"Chunk size: {args.chunk_size}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Target output directory: {args.target_output_dir}")
    
    # Split the file into chunks
    chunk_files = split_large_file(args.input_file, args.chunk_size)
    logger.info(f"Created {len(chunk_files)} chunks")
    
    # Process each chunk
    process_chunks(chunk_files, args.output, "validation", args.target_output_dir, logger)
    
    # Clean up chunk files
    for chunk_file in chunk_files:
        chunk_file.unlink()
    
    logger.success("Processing complete!")

if __name__ == "__main__":
    main() 
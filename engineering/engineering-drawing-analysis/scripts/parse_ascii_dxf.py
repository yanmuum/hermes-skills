#!/usr/bin/env python3
"""
Parse ASCII DXF engineering drawings and extract:
  - All text/TCH_TEXT entities with layers and positions
  - Tianzheng dimensions and annotations
  - Quantity table data (PUB_TAB)
  - Design specifications (路, TEXT, 文字 layers)
  - Drawing titles and index info

Usage:
  python3 parse_ascii_dxf.py drawing.dxf

Requires: nothing beyond Python stdlib (no ezdxf needed for ASCII DXF)
Encoding: auto-detects from HEADER $DWGCODEPAGE, falls back to gbk
"""

import sys
import os
from collections import Counter

def dxf_pairs(lines):
    """Convert DXF file lines to (group_code, value) pairs."""
    pairs = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        try:
            code = int(line)
            if i + 1 < len(lines):
                value = lines[i + 1].strip()
                pairs.append((code, value))
                i += 2
            else:
                i += 1
        except ValueError:
            i += 1
    return pairs


def detect_encoding(lines):
    """Detect DXF encoding from HEADER section."""
    for i, line in enumerate(lines):
        if line.strip() == '$DWGCODEPAGE':
            if i + 2 < len(lines):
                cp = lines[i + 2].strip()
                if cp.startswith('ANSI_'):
                    return 'gbk'
                elif cp == 'UTF-8':
                    return 'utf-8'
    return 'gbk'  # Default for Chinese CAD


def parse_dxf(path):
    """Parse a DXF file and return a list of entity dicts."""
    # Try GBK first, fall back to UTF-8
    for enc in ['gbk', 'utf-8']:
        try:
            with open(path, 'r', encoding=enc, errors='replace') as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue
    
    actual_enc = detect_encoding(lines)
    if actual_enc != 'gbk':
        # Re-read with detected encoding if different
        try:
            with open(path, 'r', encoding=actual_enc, errors='replace') as f:
                lines = f.readlines()
        except:
            pass  # Stick with gbk
    
    pairs = dxf_pairs(lines)
    
    # Walk pairs and collect all entities
    entities = []
    i = 0
    while i < len(pairs):
        code, value = pairs[i]
        if code == 0:  # Entity start
            entity = {'type': value}
            i += 1
            while i < len(pairs):
                c, v = pairs[i]
                entity[c] = v
                if c == 0:  # Next entity
                    break
                i += 1
            entities.append(entity)
        else:
            i += 1
    
    return entities, lines, pairs


def entity_text(entity):
    """Extract text content from an entity (code 1 or 3)."""
    return entity.get(1, entity.get(3, ''))


def by_layer(entities, target_layers):
    """Filter entities by a set of target layer names."""
    if isinstance(target_layers, str):
        target_layers = {target_layers}
    return [e for e in entities if e.get(8, '') in target_layers]


def by_type(entities, target_types):
    """Filter entities by entity type."""
    if isinstance(target_types, str):
        target_types = {target_types}
    return [e for e in entities if e['type'] in target_types]


def print_summary(entities):
    """Print a summary of all entities organized by type and layer."""
    
    # Layer statistics
    layer_counts = Counter()
    type_counts = Counter()
    for e in entities:
        layer_counts[e.get(8, '')] += 1
        type_counts[e['type']] += 1
    
    print(f"Total entities: {len(entities)}")
    print(f"Entity types: {len(type_counts)}")
    for t, c in type_counts.most_common(20):
        print(f"  {t}: {c}")
    
    print(f"\nLayers with text: {len(layer_counts)}")
    for l, c in layer_counts.most_common(15):
        print(f"  '{l}': {c} entities")
    
    # Print text content by layer
    target_text_layers = {
        'PUB_TEXT', 'PUB_TAB', 'TEXT', 'ZJ', '路', '文字',
        'DIM_LEAD', 'DIM_SYMB', '0', '0-图签', 'A-图框', 'JMD', 'SXSS'
    }
    
    for layer in sorted(target_text_layers & set(layer_counts.keys())):
        print(f"\n=== Layer '{layer}' ===")
        layer_ents = [e for e in entities if e.get(8, '') == layer]
        for e in layer_ents:
            txt = entity_text(e)
            if isinstance(txt, str) and txt.strip():
                print(f"  [{e['type']}] {txt[:100]}")
    
    # Tianzheng entities
    tch_types = [e for e in entities if e['type'].startswith('TCH_')]
    if tch_types:
        print(f"\n=== Tianzheng Entities ({len(tch_types)}) ===")
        for e in tch_types[:30]:
            txt = entity_text(e)
            dim = e.get(42, '')
            h = e.get(40, '')
            print(f"  [{e['type']}] layer={e.get(8,'?')} text='{txt[:60]}' dim={dim} h={h}")
    
    return entities


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 parse_ascii_dxf.py <drawing.dxf>")
        sys.exit(1)
    
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
    
    entities, lines, pairs = parse_dxf(path)
    print(f"File: {path}")
    print(f"Lines: {len(lines)}, Pairs: {len(pairs)}")
    print_summary(entities)

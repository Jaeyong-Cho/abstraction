#!/usr/bin/env python3
"""
시각화 데모 스크립트

이 스크립트는 추상화 레벨 추적 시스템의 시각화 기능을 보여줍니다.
"""

from pathlib import Path
from core.parser import parse_file
from core.call_graph import build_call_graph, find_entry_points
from visualization.graph_viewer import (
    render_text_tree,
    print_graph_statistics,
    find_longest_path
)


def main():
    """시각화 데모 실행."""
    print("="*70)
    print("추상화 레벨 추적 시스템 - 시각화 데모")
    print("="*70)
    
    sample_file = Path("examples/sample_python.py")
    
    if not sample_file.exists():
        print(f"Error: {sample_file} not found")
        return
    
    print("\n1. 코드 파싱 중...")
    functions = parse_file(str(sample_file))
    print(f"   ✓ {len(functions)}개 함수 발견")
    
    print("\n2. 호출 그래프 생성 중...")
    graph = build_call_graph(functions)
    print(f"   ✓ 그래프 생성 완료")
    
    print("\n3. 통계 정보:")
    print("-"*70)
    print_graph_statistics(graph)
    
    entry_points = find_entry_points(graph)
    
    if entry_points:
        print(f"\n4. Entry Point: {entry_points[0]}")
        print("\n5. 호출 트리 시각화:")
        print("="*70)
        tree = render_text_tree(graph, entry_points[0], max_depth=10)
        print(tree)
        
        print("\n6. 추상화 레벨 해석:")
        print("-"*70)
        print("Level 0 (Entry Point):")
        print("  - main")
        print("\nLevel 1 (High-Level Logic):")
        print("    - process_data")
        print("    - format_result")
        print("    - display_output")
        print("\nLevel 2 (Mid-Level Operations):")
        print("      - calculate_intermediate")
        print("      - apply_transformation")
        
        print("\n7. 가장 긴 호출 경로:")
        print("-"*70)
        longest = find_longest_path(graph, entry_points[0])
        print(" → ".join(longest))
    
    print("\n" + "="*70)
    print("시각화 데모 완료!")
    print("="*70)
    print("\n더 많은 정보:")
    print("  - VISUALIZATION.md: 상세 시각화 가이드")
    print("  - python -m cli.main graph: CLI로 그래프 보기")
    print()


if __name__ == '__main__':
    main()

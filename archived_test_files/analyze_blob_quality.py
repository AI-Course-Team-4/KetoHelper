#!/usr/bin/env python3
"""
생성된 blob들의 품질 분석
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from approach1_title_blob.approach1_supabase import TitleBlobApproachSupabase
from approach2_no_title_blob.approach2_supabase import NoTitleBlobApproachSupabase
from approach3_llm_preprocessing.approach3_supabase import LLMPreprocessingApproachSupabase
import json

def analyze_blob_quality():
    """생성된 blob들의 품질 분석"""
    print("=== Blob 품질 분석 시작 ===\n")
    
    # 각 방식별 접근자 초기화
    approach1 = TitleBlobApproachSupabase()
    approach2 = NoTitleBlobApproachSupabase()
    approach3 = LLMPreprocessingApproachSupabase()
    
    approaches = [
        ("방식1 (Title + Blob)", approach1, "recipes_title_blob"),
        ("방식2 (No Title + Blob)", approach2, "recipes_no_title_blob"),
        ("방식3 (LLM Preprocessing)", approach3, "recipes_llm_preprocessing")
    ]
    
    for approach_name, approach, table_name in approaches:
        print(f"=== {approach_name} 분석 ===")
        
        try:
            # 테이블에서 데이터 조회
            result = approach.supabase.table(table_name).select('*').limit(5).execute()
            
            if result.data:
                print(f"총 데이터 수: {len(result.data)}개 (샘플 5개 분석)")
                print()
                
                for i, row in enumerate(result.data, 1):
                    print(f"--- 샘플 {i} ---")
                    print(f"레시피 ID: {row.get('recipe_id', 'N/A')}")
                    print(f"제목: {row.get('title', 'N/A')}")
                    
                    # blob 내용 분석
                    processed_content = row.get('processed_content', '')
                    if processed_content:
                        if isinstance(processed_content, str):
                            try:
                                processed_content = json.loads(processed_content)
                            except:
                                pass
                        
                        print(f"처리된 내용 타입: {type(processed_content)}")
                        
                        if isinstance(processed_content, dict):
                            print("처리된 내용 구조:")
                            for key, value in processed_content.items():
                                if isinstance(value, list):
                                    print(f"  {key}: {value[:3]}{'...' if len(value) > 3 else ''} (총 {len(value)}개)")
                                else:
                                    print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                        else:
                            print(f"처리된 내용: {str(processed_content)[:200]}{'...' if len(str(processed_content)) > 200 else ''}")
                    
                    # 메타데이터 분석
                    metadata = row.get('metadata', {})
                    if metadata:
                        print(f"메타데이터: {metadata}")
                    
                    # 임베딩 정보
                    embedding = row.get('embedding')
                    if embedding:
                        print(f"임베딩 차원: {len(embedding) if isinstance(embedding, list) else 'N/A'}")
                    
                    print()
                
                # 전체 통계
                all_data = approach.supabase.table(table_name).select('*').execute()
                total_count = len(all_data.data)
                
                # blob 길이 통계
                blob_lengths = []
                for row in all_data.data:
                    metadata = row.get('metadata', {})
                    if isinstance(metadata, dict) and 'blob_length' in metadata:
                        blob_lengths.append(metadata['blob_length'])
                
                if blob_lengths:
                    avg_length = sum(blob_lengths) / len(blob_lengths)
                    min_length = min(blob_lengths)
                    max_length = max(blob_lengths)
                    
                    print(f"📊 통계:")
                    print(f"  - 총 레시피 수: {total_count}")
                    print(f"  - 평균 blob 길이: {avg_length:.1f}자")
                    print(f"  - 최소 blob 길이: {min_length}자")
                    print(f"  - 최대 blob 길이: {max_length}자")
                
            else:
                print("데이터가 없습니다.")
                
        except Exception as e:
            print(f"분석 중 오류: {e}")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    analyze_blob_quality()

import warnings
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

def search_web(query):
    if DDGS is None:
        return "검색 오류: duckduckgo-search 패키지가 설치되지 않았습니다. 터미널에서 'uv add duckduckgo-search' 또는 'pip install duckduckgo-search'를 실행하세요."
    try:
        results = list(DDGS().text(query, max_results=5))
        if not results:
            return f"검색 결과가 없습니다: {query}"
        formatted_results = "\n\n".join([f"제목: {r.get('title')}\n내용: {r.get('body')}\n링크: {r.get('href')}" for r in results])
        return f"'{query}' 웹 검색 결과:\n{formatted_results}"
    except Exception as e:
        return f"검색 오류: {e}"

def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 4000:
                return content[:4000] + "\n\n[주의: 내용이 너무 길어 4000자로 잘렸습니다. 필요한 부분만 구체적으로 다시 요청하거나 다른 도구를 활용하세요.]"
            return content
    except FileNotFoundError:
        return f"파일 오류: '{filepath}' 파일을 찾을 수 없습니다."
    except Exception as e:
        return f"읽기 오류: {e}"

def append_file(filepath, content):
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write("\n" + content)
        return f"'{filepath}' 파일에 성공적으로 내용을 추가했습니다."
    except Exception as e:
        return f"추가 오류: {e}"

def write_file(filepath, content):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"'{filepath}' 파일이 성공적으로 작성되었습니다."
    except Exception as e:
        return f"쓰기 오류: {e}"

def modify_file(filepath, old_str, new_str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if old_str not in content:
            return f"수정 오류: '{old_str}'을(를) 파일에서 정확히 찾을 수 없습니다. 들여쓰기나 줄바꿈이 다른지 확인해 주시고, 잦은 수정 실패 시 write_file로 전체 내용을 덮어쓰는 것을 고려하세요."
            
        match_count = content.count(old_str)
        if match_count > 1:
            return f"수정 오류: '{old_str}' 문구가 파일 내에 여러 번({match_count}회) 존재합니다. 의도치 않은 영역이 수정되지 않도록 더 구체적이고 긴 문자열을 'old_str'로 지정해 주세요."
            
        content = content.replace(old_str, new_str)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"'{filepath}' 파일이 성공적으로 수정되었습니다."
    except FileNotFoundError:
        return f"파일 오류: '{filepath}' 파일을 찾을 수 없습니다."
    except Exception as e:
        return f"수정 오류: {e}"

import urllib.request
import urllib.parse
import urllib.error
import re

def search_namuwiki(keyword):
    """
    나무위키에서 주어진 키워드로 검색하여 본문 텍스트를 추출하는 도구
    """
    url = f"https://namu.wiki/w/{urllib.parse.quote(keyword)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        # 간단한 정규식으로 태그와 스크립트 제거
        text = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<.*?>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 앞부분 불필요한 내용 스킵용 간단 휴리스틱
        if keyword in text:
            start_idx = text.find(keyword)
            text = text[start_idx:]
            
        return f"'{keyword}' 나무위키 문서 내용 (일부):\n{text[:4000]}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"나무위키 검색 오류: '{keyword}' 문서가 존재하지 않습니다."
        elif e.code == 403:
            return f"나무위키 검색 오류: 접근이 거부되었습니다. (크롤링 차단)"
        return f"나무위키 검색 HTTP 오류: {e}"
    except Exception as e:
         return f"나무위키 검색 오류: {e}"

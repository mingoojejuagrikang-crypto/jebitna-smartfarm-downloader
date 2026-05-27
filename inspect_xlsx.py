import os
import glob
import openpyxl

def inspect():
    # test_downloads 폴더 안의 xlsx 파일들 검색
    files = glob.glob("./test_downloads/*.xlsx")
    if not files:
        # 혹시 downloads 폴더 내에 저장된 파일이 있는지 검색
        files = glob.glob("./downloads/**/*.xlsx", recursive=True)
        
    if not files:
        print("[!] No excel files found to inspect.")
        return
        
    target_xlsx = files[0]
    print(f"[*] Inspecting file: {target_xlsx}")
    
    wb = openpyxl.load_workbook(target_xlsx, data_only=True)
    sheet = wb.active
    print(f"[*] Sheet Name: {sheet.title}")
    
    # 첫 10개 행 읽어오기
    rows = []
    for idx, r in enumerate(sheet.iter_rows(values_only=True)):
        if idx >= 15:
            break
        rows.append(r)
    print(f"[*] Read {len(rows)} rows:")
    for idx, r in enumerate(rows):
        print(f"  Row [{idx}]: {r}")
        
if __name__ == "__main__":
    inspect()

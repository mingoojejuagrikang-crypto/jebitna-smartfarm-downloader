import requests
import json

def test_api():
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJ1c2VySW5kZXgiOjEwNSwiYXV0aG9yaXR5IjoiUk9MRV9HUk9XVEhfTUFOQUdFUiIsImlzTmV3IjpmYWxzZSwiZXhwIjoxNzc5ODY3ODQzLCJ1c2VySWQiOiJrYWxzcm4ifQ.FzuCF_Ps3T5F1EFmRLzsoPiDRKCoijBADXFhjmpY9HaFDMsLGAGIhLn3QASRaMeTSCpB0NwieZYTmAZJZNTn_A"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    
    # 1. 농가 목록 조회 API 호출
    farms_url = "https://jebitna.agri.jeju.kr/api/farms/readall"
    print(f"[*] Calling Farms API: {farms_url}")
    res = requests.get(farms_url, headers=headers)
    print(f"[*] Status: {res.status_code}")
    
    if res.status_code != 200:
        print("[!] Failed to fetch farms.")
        return
        
    farms_data = res.json()
    print(f"[*] Raw Farms Data: {json.dumps(farms_data, ensure_ascii=False)}")
    print(f"[*] Found {len(farms_data)} farms:")
    for farm in farms_data:
        # 실제 JSON에서 인덱스 키와 이름을 확인해봅니다.
        # farmIndex, id, index, idx, key 등 다양한 가능성 조사
        name = farm.get('farmName') or farm.get('name')
        idx = farm.get('farmIndex') or farm.get('farmIdx') or farm.get('id') or farm.get('index') or farm.get('idx')
        print(f"  - Farm Name: {name}, Detected Index: {idx}")
        
    # 2. 첫 번째 농가의 장치/센서 목록 조회
    if farms_data:
        target_farm = farms_data[0]
        farm_idx = target_farm.get('farmIndex') or target_farm.get('farmIdx') or target_farm.get('id') or target_farm.get('index') or target_farm.get('idx')
        sensors_url = f"https://jebitna.agri.jeju.kr/api/monitor/target-list?farmIndex={farm_idx}"
        print(f"\n[*] Calling Sensors API: {sensors_url}")
        res_sensors = requests.get(sensors_url, headers=headers)
        print(f"[*] Status: {res_sensors.status_code}")
        
        if res_sensors.status_code == 200:
            sensors_data = res_sensors.json()
            print(f"[*] Raw Sensors Response Keys: {list(sensors_data.keys())}")
            sensors = sensors_data.get("sensors", [])
            devices = sensors_data.get("devices", [])
            print(f"[*] Found {len(sensors)} sensors in list.")
            print(f"[*] Found {len(devices)} devices in list.")
            if sensors:
                print(f"[*] Sample Sensor: {json.dumps(sensors[0], ensure_ascii=False)}")
            if devices:
                print(f"[*] Sample Device: {json.dumps(devices[0], ensure_ascii=False)}")
            
            # 3. 1주치 원시 데이터 조회 API 호출
            # 각 구역(sensors) 객체 내부의 devices 리스트에서 index 추출
            sensor_ids = []
            for area in sensors_data.get("sensors", []):
                for dev in area.get("devices", []):
                    if dev.get("index"):
                        sensor_ids.append(dev.get("index"))
            
            device_ids = []
            for area in sensors_data.get("devices", []):
                for dev in area.get("devices", []):
                    if dev.get("index"):
                        device_ids.append(dev.get("index"))
                        
            sensor_ids_str = ",".join(sensor_ids)
            device_ids_str = ",".join(device_ids)
            
            record_url = f"https://jebitna.agri.jeju.kr/api/monitor/record?devices={device_ids_str}&sensors={sensor_ids_str}&begin=2026-05-01&end=2026-05-27"
            print(f"\n[*] Calling Record API: {record_url[:150]}...")
            
            res_record = requests.get(record_url, headers=headers)
            print(f"[*] Status: {res_record.status_code}")
            if res_record.status_code == 200:
                record_data = res_record.json()
                print(f"[*] Keys in response: {list(record_data.keys())}")
                
                sensor_table = record_data.get("sensorTable", [])
                device_table = record_data.get("deviceTable", [])
                
                print(f"[*] sensorTable rows: {len(sensor_table)}")
                print(f"[*] deviceTable rows: {len(device_table)}")
                
                if sensor_table:
                    print(f"[*] Sample sensorTable Rows (first 2):")
                    for row in sensor_table[:2]:
                        print(f"  {json.dumps(row, ensure_ascii=False)}")
                if device_table:
                    print(f"[*] Sample deviceTable Rows (first 2):")
                    for row in device_table[:2]:
                        print(f"  {json.dumps(row, ensure_ascii=False)}")
            else:
                print(f"[!] Record API returned error: {res_record.text}")

if __name__ == "__main__":
    test_api()

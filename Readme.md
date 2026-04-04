***
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-0078D6?logo=windows&logoColor=white)
![Stockfish](https://img.shields.io/badge/Evaluated_by-Stockfish-4B514D?logo=chess)
---

## Yêu cầu hệ thống:
- **Ngôn ngữ:** Python 3.10+
- **Hệ điều hành:** Windows 

## Requirements

- Tạo môi trường ảo (virtual environment)
```
# Windows
py -m venv venv

# Linux / macOS:
python3 -m venv venv
```

- Kích hoạt môi trường ảo
```
# Windows
venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

- Cài đặt các thư viện từ `requirements.txt`
```
pip install -r requirements.txt
```

- Sử dụng stockfish để đo độ chính xác của từng bot
```
python .\evaluate.py
```
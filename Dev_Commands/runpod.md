# Runpod Commands

1.python3 -m venv venv

2.source venv/bin/activate

3.pip install -r requirements.txt

4.To Start the fast api server for gemma 3n : python gemma_server.py this will run in port 8000

5.uvicorn main:app --host 0.0.0.0 --port 8081 --reload

6.uvicorn main:app --host 0.0.0.0 --port 38277 --reload

7.cd workspace && source venv/bin/activate && cd Gemma_Server && python gemma_server.py

8.cd workspace && source venv/bin/activate && cd Gemma_Kavach_Vision_Server && uvicorn main:app --host 0.0.0.0 --port 38277 --reload
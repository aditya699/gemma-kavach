# Runpod Commands

1.python3 -m venv venv

2.source venv/bin/activate

3.pip install -r requirements.txt

4.To Start the fast api server for gemma 3n : python gemma_server.py this will run in port 8000

5.uvicorn main:app --host 0.0.0.0 --port 8081 --reload

6.uvicorn main:app --host 0.0.0.0 --port 38277 --reload

7.cd workspace && source venv/bin/activate && cd GemmaServer && python gemma_server.py

8.cd workspace && source venv/bin/activate && cd Gemma_Kavach_Vision_Server && uvicorn main:app --host 0.0.0.0 --port 38277 --reload

9.cd workspace && source venv/bin/activate && cd Gemma_Kavach_Vision_Server && uvicorn main:app --host 0.0.0.0 --port 38277 --reload

10.cd workspace && source venv/bin/activate && cd Gemma_Kavach_Voice_Server && uvicorn main:app --host 0.0.0.0 --port 7860 --reload

11.Force delete command in rm -rf Gemma_Kavach_Voice_Server

12.run this command: nohup python job.py >> train.log 2>&1 &

13.ps aux | grep job.py  (check if the job is running)

14.tail -f train.log (check actual logs)

15.cd workspace && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

FROM python:3.13

WORKDIR /docker

COPY src/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ["src/service/*.py", "./service/"]
COPY ["src/utils/*.py", "src/utils/model.bin", "./utils/"]

EXPOSE 8080

ENTRYPOINT ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8080"]
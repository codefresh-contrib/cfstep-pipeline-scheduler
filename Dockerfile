FROM python:3.6.4-alpine3.7

ENV LANG C.UTF-8

RUN pip install requests

COPY lib/schedule.py /schedule.py

ENTRYPOINT ["python", "/schedule.py"]
CMD [""]
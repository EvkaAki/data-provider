FROM python
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN mkdir keys
RUN ssh-keygen -t rsa -m PEM -f keys/id_rsa
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
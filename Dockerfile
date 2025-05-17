FROM bitnami/spark:latest

USER root

# Install Python and dependencies
RUN install_packages python3 python3-pip
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Copy app
#WORKDIR /app
#COPY . /app

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

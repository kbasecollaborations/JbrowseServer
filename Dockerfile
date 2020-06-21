FROM python:3.7-slim-stretch


ARG DEVELOPMENT

RUN apt-get update -y && apt-get install -y samtools

WORKDIR /kb/module
COPY requirements.txt /kb/module/requirements.txt
COPY dev-requirements.txt /kb/module/dev-requirements.txt
WORKDIR /kb/module
RUN pip install --upgrade pip && \
    pip install pandas==0.24.1 && \
    pip install --upgrade --extra-index-url https://pypi.anaconda.org/kbase/simple \
      -r requirements.txt \
      kbase-workspace-client==0.3.0 \
      kbase_cache_client==0.0.2 && \
    if [ "$DEVELOPMENT" ]; then pip install -r dev-requirements.txt; fi

RUN pip install flask-cors
# Run the server
COPY . /kb/module

RUN mkdir -p /kb/module/work
#ADD src/static /kb/module/work

#See .env.example for template for .env
#COPY .env.example /kb/module/.env



RUN chmod -R a+rw /kb/module
EXPOSE 5000
ENTRYPOINT ["sh", "/kb/module/entrypoint.sh"]

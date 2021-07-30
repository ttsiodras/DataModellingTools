FROM debian:buster

RUN bash -c "echo -e 'Acquire::http::Pipeline-Depth 0;\nAcquire::http::No-Cache true;\nAcquire::BrokenProxy true;\n' > /etc/apt/apt.conf.d/99badproxies"
RUN cat  /etc/apt/apt.conf.d/99badproxies
RUN apt-get update
RUN apt-get install -y libxslt-dev libxml2-dev python-psycopg2 mono-runtime libmono-system-data4.0-cil libmono-system-web4.0-cil libfsharp-core4.3-cil libpq-dev python3 python3-distutils
RUN apt-get install -y wget python3-pip
RUN wget -O - -q https://github.com/ttsiodras/asn1scc/releases/download/4.2.0.1.f/asn1scc-bin-4.2.0.1f.tar.bz2 | tar jxvf -
RUN apt-get install -y python-pip
RUN wget -O - -q https://github.com/ttsiodras/DataModellingTools/files/335591/antlr-2.7.7.tar.gz | tar zxvf - ; cd antlr-2.7.7/lib/python ; pip2 install .
RUN pip2 install --upgrade SQLAlchemy psycopg2
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
RUN apt-get install less
RUN apt-get install -y postgresql
COPY setup_testdb.sh /tmp/
RUN /tmp/setup_testdb.sh

FROM phusion/baseimage:jammy-1.0.4
LABEL Name=handle_server_postgres Version=1.0.0

## Image config

# Use baseimage-docker's init process.
CMD ["/sbin/my_init"]

# Update installed APT packages
RUN add-apt-repository ppa:openjdk-r/ppa
RUN apt-get update && apt-get upgrade -y -o Dpkg::Options::="--force-confold"

RUN apt-get install -y ntp wget openjdk-11-jdk python3 libpostgresql-jdbc-java

# Install pip and Python packages (psycopg2 is optional but helpful for testing or debugging)
RUN apt-get install -y python3-pip
RUN pip3 install psycopg2-binary jinja2

# Cleanup
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

## Handle Server setup

# Get the handle server package and put it in the container
ADD http://handle.net/hnr-source/handle-9.3.2-distribution.tar.gz /tmp/
RUN mkdir -p /opt/handle && tar xf /tmp/handle-9.3.2-distribution.tar.gz -C /opt/handle --strip-components=1

# Add the PostgreSQL JDBC connector
RUN cp /usr/share/java/postgresql.jar /opt/handle/lib/postgresql.jar

# Copy directory with server configuration templates and python build script
COPY config/ /home/handle/config/
COPY scripts/ /home/handle/

# Create the working directory for the handle server
RUN mkdir -p /var/handle/svr

# Create webapps directory and copy admin.war for web interface
RUN mkdir -p /var/handle/svr/webapps
RUN cp /opt/handle/admin.war /var/handle/svr/webapps/

# Create logs directory and redirect log files to stdout/stderr
RUN mkdir -p /var/handle/svr/logs \
    && ln -sf /dev/stdout /var/handle/svr/logs/access.log \
    && ln -sf /dev/stderr /var/handle/svr/logs/error.log

# Install Handle server as a service
RUN mkdir /etc/service/handle
COPY scripts/handle.sh /etc/service/handle/run
RUN chmod +x /etc/service/handle/run

# Assure Unix line endings (LF) even if created on a windows machine
RUN sed -i 's/\r$//' /etc/service/handle/run

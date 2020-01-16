/etc/init.d/postgresql start
su - postgres -c 'createuser ubuntu;'
echo "ALTER USER ubuntu WITH PASSWORD 'tastedb';" | su - postgres -c 'psql -w'
echo '127.0.0.1:5432:*:ubuntu:tastedb' > ~/.pgpass
chmod 0600 ~/.pgpass
echo "GRANT ALL PRIVILEGES ON DATABASE postgres TO ubuntu;" | su - postgres -c 'psql -w'
echo "ALTER USER ubuntu CREATEDB;" | su - postgres -c 'psql -w'

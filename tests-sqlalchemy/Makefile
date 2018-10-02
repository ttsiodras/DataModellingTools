all:	cleanDB test

cleanDB:
	# PostgreSQL
	/etc/init.d/postgresql restart
	# Since postgres takes a while to start, do this until it succeeds
	bash -c "while true ; do echo 'drop database if exists circle_test; create database circle_test;' | psql -h 127.0.0.1 -U ubuntu postgres && break ; done"
	rm -f sql.log
	#
	# MySQL (is a toy - disabled related tests)
	# echo 'drop database test; create database test;' | mysql -u taste || exit 1
	#
	# SQLite
	rm -f test.db

clean:
	rm -rf asn2dataModel lotsofdatatypes_model.* */*.pyc .coverage
	$(MAKE) cleanDB

build:
	if [ ! -d asn2dataModel ] ; then mkdir -p asn2dataModel ; LC_ALL=C asn2dataModel -o asn2dataModel -toPython LotsOfDataTypes.asn ; fi
	cd asn2dataModel || exit 1 && make -f Makefile.python
	LC_ALL=C asn2dataModel -toSqlalchemy -o asn2dataModel/ LotsOfDataTypes.asn

debug:	|build
	ipdb -m ./testSQLengines.py

test:	|build
	./testSQLengines.py

print:
	@for i in MyInt My2ndInt MySeq MyChoice TypeEnumerated MySuperSeq T_ARR T_ARR_indexes T_ARR_elm ; do \
	    	echo "========" ; \
		echo PostgreSQL Content of $$i ; \
		echo "========" ; \
		echo "select * from \"$$i\" " | psql -h 127.0.0.1 -U ubuntu circle_test ; \
	done
#	@for i in MyInt My2ndInt MySeq MyChoice TypeEnumerated MySuperSeq T_ARR T_ARR_indexes T_ARR_elm ; do \
#	    	echo "========" ; \
#		echo MySQL Content of $$i ; \
#		echo "========" ; \
#		echo "select * from $$i " | mysql -u taste test ; \
#	done | less
	@for i in MyInt My2ndInt MySeq MyChoice TypeEnumerated MySuperSeq T_ARR T_ARR_indexes T_ARR_elm ; do \
	    	echo "========" ; \
		echo SQLite Content of $$i ; \
		echo "========" ; \
		echo "select * from $$i ;" | sqlite3 test.db ; \
	done

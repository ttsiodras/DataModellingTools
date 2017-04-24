all:	cleanDB test

cleanDB:
	# PostgreSQL
	echo 'drop database circle_test; create database circle_test;' | psql -h 127.0.0.1 -U ubuntu postgres || exit 1
	rm -f sql.log
	#
	# MySQL (is a toy - disabled related tests)
	# echo 'drop database test; create database test;' | mysql -u taste || exit 1
	#
	# SQLite
	rm -f test.db

clean:
	rm -rf verifier/asn2dataModel verifier/lotsofdatatypes_model.* */*.pyc verifier/LotsOfDataTypes.asn .coverage
	$(MAKE) cleanDB

build:
	cd verifier/ ; if [ ! -d asn2dataModel ] ; then mkdir -p asn2dataModel ; [ ! -h LotsOfDataTypes.asn ] && ln -s ../LotsOfDataTypes.asn ; LC_ALL=C asn2dataModel -o asn2dataModel -toPython LotsOfDataTypes.asn ; fi
	cd verifier/asn2dataModel || exit 1 && make -f Makefile.python
	cd verifier ; LC_ALL=C asn2dataModel -toSqlalchemy -o asn2dataModel/ LotsOfDataTypes.asn
	touch verifier/asn2dataModel/__init__.py

debug:	|build
	ipdb -m verifier.testSQLengines.py 

test:	|build
	python -m verifier.testSQLengines

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

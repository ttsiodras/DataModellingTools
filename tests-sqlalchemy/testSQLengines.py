#!/usr/bin/env python2
import os
import sys
sys.path.append("asn2dataModel")

import logging
import unittest

from sqlalchemy import create_engine

from commonTests import AllTests
from lotsofdatatypes_model import Base

from lotsofdatatypes_model import My2ndInt_SQL
from LotsOfDataTypes_asn import My2ndInt

logging.basicConfig(filename="sql.log")
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class CompleteTestingOfSQLMapperWithSQLite(AllTests, unittest.TestCase):
    #engine = create_engine('sqlite:///:memory:', echo=True)
    engine = create_engine('sqlite:///test.db', echo=False)
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker

    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()


class CompleteTestingOfSQLMapperWithPostgreSQL(AllTests, unittest.TestCase):
    #engine = create_engine('sqlite:///:memory:', echo=True)
    if os.getenv('CIRCLECI') is None:
        dburi = 'postgresql+psycopg2://ubuntu:tastedb@localhost/circle_test'
    else:
        dburi = 'postgresql+psycopg2://ubuntu:@localhost/circle_test'
    engine = create_engine(dburi, echo=False)
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker

    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()


#jclass CompleteTestingOfSQLMapperWithMySQL(AllTests, unittest.TestCase):
#j    #engine = create_engine('sqlite:///:memory:', echo=True)
#j    engine = create_engine(
#j        'mysql://taste:tastedb@localhost/test', echo=False)
#j    Base.metadata.create_all(engine)
#j    from sqlalchemy.orm import sessionmaker
#j
#j    SessionFactory = sessionmaker(bind=engine)
#j    session = SessionFactory()
#j
#j    def test2_IntegerWithOverridenConstraints(self):
#j        a = My2ndInt()
#j        #
#j        # MySQL does not enforce range constraints.
#j        # Stupid DB engine...
#j        #
#j        ##a.Set(20)  # Valid in referenced type, but overriden in this one
#j        ##bMustFailAndHasFailed = False
#j        ##try:
#j        ##    aa2 = My2ndInt_SQL(a)
#j        ##    aid2 = aa2.save(self.session)
#j        ##except exc.IntegrityError:
#j        ##    bMustFailAndHasFailed = True
#j        ##assert bMustFailAndHasFailed
#j        self.session.rollback()
#j        a.Set(7)
#j        aa2 = My2ndInt_SQL(a)
#j        aid2 = aa2.save(self.session)
#j        self.session.commit()
#j        o2 = My2ndInt_SQL.loadFromDB(self.session, aid2)
#j        assert a.Get() == o2.data
#j        assert a.Get() == o2.asn1.Get()


if __name__ == "__main__":
    unittest.main()

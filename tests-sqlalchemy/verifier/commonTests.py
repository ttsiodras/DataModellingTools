import sys
import math

from sqlalchemy import exc

# sys.path.append("asn2dataModel")
from .asn2dataModel import DV
from .asn2dataModel.lotsofdatatypes_model import (
    MyInt_SQL, My2ndInt_SQL, MySeq_SQL, TypeEnumerated_SQL, T_ARR_SQL,
    MySuperSeq_SQL, MyChoice_SQL, TypeNested_SQL)
from .asn2dataModel.LotsOfDataTypes_asn import (
    MyInt, My2ndInt, MySeq, TypeEnumerated, T_ARR, MySuperSeq, MyChoice,
    TypeNested
)


class AllTests:
    def test1_Integer(self):
        a = MyInt()
        a.Set(2)
        aa1 = MyInt_SQL(a)
        aid1 = aa1.save(self.session)
        self.session.commit()
        o1 = MyInt_SQL.loadFromDB(self.session, aid1)
        assert a.Get() == o1.data
        assert a.Get() == o1.asn1.Get()

    def test2_IntegerWithOverridenConstraints(self):
        a = My2ndInt()
        a.Set(20)  # Valid in referenced type, but overriden in this one
        bMustFailAndHasFailed = False
        try:
            aa2 = My2ndInt_SQL(a)
            aid2 = aa2.save(self.session)
        except exc.IntegrityError:
            bMustFailAndHasFailed = True
        assert bMustFailAndHasFailed
        self.session.rollback()
        a.Set(7)
        aa2 = My2ndInt_SQL(a)
        aid2 = aa2.save(self.session)
        self.session.commit()
        o2 = My2ndInt_SQL.loadFromDB(self.session, aid2)
        assert a.Get() == o2.data
        assert a.Get() == o2.asn1.Get()

    def test3_SimpleSequence(self):
        b = MySeq()
        b.anInt.Set(16)
        b.anotherInt.Set(17)
        bb = MySeq_SQL(b)
        bid = bb.save(self.session)
        self.session.commit()
        z = MySeq_SQL.loadFromDB(self.session, bid)
        # Via SQLAlchemy
        assert b.anInt.Get() == z.anInt.data
        assert b.anotherInt.Get() == z.anotherInt.data
        # Via ASN.1
        assert b.anInt.Get() == z.asn1.anInt.Get()
        assert b.anotherInt.Get() == z.asn1.anotherInt.Get()

    def test4_Choice(self):
        g = MyChoice()
        g.kind.Set(DV.MyChoice_anInt_PRESENT)
        g.anInt.Set(12)
        gg = MyChoice_SQL(g)
        gid = gg.save(self.session)
        self.session.commit()
        r = MyChoice_SQL.loadFromDB(self.session, gid)
        assert g.kind.Get() == r.kind
        assert g.anInt.Get() == r.anInt.data
        assert g.kind.Get() == r.asn1.kind.Get()
        assert g.anInt.Get() == r.asn1.anInt.Get()

    def test5_Enumerated(self):
        c = TypeEnumerated()
        c.Set(TypeEnumerated.blue)
        cc = TypeEnumerated_SQL(c)
        cid = cc.save(self.session)
        self.session.commit()
        w = TypeEnumerated_SQL.loadFromDB(self.session, cid)
        assert c.Get() == w.data
        assert c.Get() == w.asn1.Get()

    def test6_ArrayOfInts(self):
        e = T_ARR()
        e.SetLength(6)
        for i in xrange(6):
            e[i].Set(i*3)
        ee = T_ARR_SQL(e)
        eid = ee.save(self.session)
        self.session.commit()
        x = T_ARR_SQL.loadFromDB(self.session, eid)
        xa = x.asn1
        for idx, idxObj in enumerate(x.arrIndexes_T_ARR):
            assert e[idx].Get() == idxObj.data.data
            assert e[idx].Get() == xa[idx].Get()

    def test7_ComplexTypeWithNestedNestedArrays(self):
        d = MySuperSeq()
        d.aSeq.anInt.Set(11)
        d.aSeq.anotherInt.Set(12)
        d.anotherSeq.anInt.Set(13)
        d.anotherSeq.anotherInt.Set(14)
        d.anArray.SetLength(6)
        for i in xrange(6):
            #d.anArray[i].SetLength(7)
            for j in xrange(7):
                d.anArray[i][j].Set(i*j + 0.5)
        d.aString.SetFromPyString("Hello")
        dd = MySuperSeq_SQL(d)
        did = dd.save(self.session)
        self.session.commit()

        y = MySuperSeq_SQL.loadFromDB(self.session, did)
        assert d.aSeq.anInt.Get() == y.aSeq.anInt.data
        assert d.aSeq.anotherInt.Get() == y.aSeq.anotherInt.data
        assert d.anotherSeq.anInt.Get() == y.anotherSeq.anInt.data
        assert d.anotherSeq.anotherInt.Get() == y.anotherSeq.anotherInt.data
        assert d.aString.GetPyString() == y.aString.data

        yy = y.asn1
        assert d.aSeq.anInt.Get() == yy.aSeq.anInt.Get()
        assert d.aSeq.anotherInt.Get() == yy.aSeq.anotherInt.Get()
        assert d.anotherSeq.anInt.Get() == yy.anotherSeq.anInt.Get()
        assert d.anotherSeq.anotherInt.Get() == yy.anotherSeq.anotherInt.Get()
        assert d.anArray.GetLength() == yy.anArray.GetLength()
        for i in xrange(6):
            assert d.anArray[i].GetLength() == yy.anArray[i].GetLength()
            for j in xrange(7):
                assert d.anArray[i][j].Get() == yy.anArray[i][j].Get()
        assert d.aString.GetPyString() == yy.aString.GetPyString()

    def test8_VeryComplexType(self):
        e = TypeNested()
        e.intVal.Set(5),
        e.int2Val.Set(-10)
        e.int3Val.Set(12)
        for i in xrange(10):
            e.intArray[i].Set(i%4)
            e.realArray[i].Set(0.1+0.1*i)
            e.octStrArray[i].SetFromPyString('hello' + str(i))
            e.boolArray[i].Set(i%2 != 0)
            e.enumArray[i].Set(TypeEnumerated.blue)
        e.enumValue.Set(TypeEnumerated.red)
        e.enumValue2.Set(DV.truism)
        e.label.SetFromPyString("Well, this is nice")
        e.bAlpha.Set(False)
        e.bBeta.Set(True)
        e.sString.SetFromPyString("Another string")
        e.arr.SetLength(5)
        e.arr2.SetLength(5)
        for i in xrange(5):
            e.arr[i].Set(41*i)
            e.arr2[i].Set(0.1+0.1*i)
        ee = TypeNested_SQL(e)
        eid = ee.save(self.session)
        self.session.commit()
        
        f = TypeNested_SQL.loadFromDB(self.session, eid)
        ff = f.asn1
        assert e.intVal.Get() == ff.intVal.Get()
        assert e.int2Val.Get() == ff.int2Val.Get()
        assert e.int3Val.Get() == ff.int3Val.Get()
        for i in xrange(10):
            assert e.intArray[i].Get() == ff.intArray[i].Get()
            assert math.fabs(e.realArray[i].Get() - ff.realArray[i].Get())<1e-10
            assert e.octStrArray[i].GetPyString() == ff.octStrArray[i].GetPyString()
            assert e.boolArray[i].Get() == ff.boolArray[i].Get()
            assert e.enumArray[i].Get() == ff.enumArray[i].Get()
        assert e.enumValue.Get() == ff.enumValue.Get()
        assert e.enumValue2.Get() == ff.enumValue2.Get()
        assert e.label.GetPyString() == ff.label.GetPyString()
        assert e.bAlpha.Get() == ff.bAlpha.Get()
        assert e.bBeta.Get() == ff.bBeta.Get()
        assert e.sString.GetPyString() == ff.sString.GetPyString()
        assert ff.arr.GetLength() == 5
        assert ff.arr2.GetLength() == 5
        for i in xrange(5):
            assert e.arr[i].Get() == ff.arr[i].Get()
            assert math.fabs(e.arr2[i].Get() - ff.arr2[i].Get()) < 1e-10

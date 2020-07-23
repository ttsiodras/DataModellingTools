.PHONY:	M2M M2C clean

all:	M2M M2C

M2M:
	$(MAKE) -f Makefile.M2M clean
	$(MAKE) -f Makefile.M2M

M2C:
	$(MAKE) -f Makefile.M2C clean
	$(MAKE) -f Makefile.M2C

SMP2:
	$(MAKE) -f Makefile.SMP2 clean
	$(MAKE) -f Makefile.SMP2

clean:
	$(MAKE) -f Makefile.M2M clean
	$(MAKE) -f Makefile.M2C clean
	$(MAKE) -f Makefile.SMP2 clean

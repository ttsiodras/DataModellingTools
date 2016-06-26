template = '''
SUBPROGRAM mytestsubsystem%(name)s_PI
FEATURES
        my_in_%(name)s:IN PARAMETER DataView::%(name)s {encoding=>UPER;};
END mytestsubsystem%(name)s_PI;

SUBPROGRAM IMPLEMENTATION mytestsubsystem%(name)s_PI.GUIPI
PROPERTIES
        FV_Name => "mytestsubsystem%(name)s_fv_GUIPI";
        Source_Language => GUI_PI;
END mytestsubsystem%(name)s_PI.GUIPI;



SUBPROGRAM mytestsubsystem%(name)s_RI
FEATURES
        my_in_%(name)s:IN PARAMETER DataView::%(name)s {encoding=>UPER;};
END mytestsubsystem%(name)s_RI;

SUBPROGRAM IMPLEMENTATION mytestsubsystem%(name)s_RI.GUIRI
PROPERTIES
        FV_Name => "mytestsubsystem%(name)s_fv_GUIRI";
        Source_Language => GUI_RI;
END mytestsubsystem%(name)s_RI.GUIRI;

'''

mytypes = [
    'AType',
    'TypeEnumerated',
    'TypeNested',
    'T_POS',
    'T_POS_SET',
    'T_ARR',
    'T_ARR2',
    'T_ARR3',
    'T_ARR4',
    'T_SET',
    'T_SETOF',
    'T_BOOL',
    'T_INT',
    'T_REAL',
    'T_STRING',
    'T_META'
]

for t in mytypes:
    print template % {'name':t}

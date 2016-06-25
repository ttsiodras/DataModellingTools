#
# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the suggested version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to comply
# with the terms of the GNU Lesser General Public License version 2.1.
#
# GNU LGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# applications, when you are willing to comply with the terms of the
# GNU Lesser General Public License version 2.1.
#
# Note that in both cases, there are no charges (royalties) for the
# generated code.
#
import re
import os

from typing import Set, IO, Any  # NOQA pylint: disable=unused-import

from ..commonPy.asnAST import (
    AsnBasicNode, AsnEnumerated, AsnSequence, AsnSet, AsnChoice,
    AsnSequenceOf, AsnSetOf, AsnMetaMember, AsnInt, AsnReal, AsnOctetString,
    AsnBool, isSequenceVariable, sourceSequenceLimit)
from ..commonPy.utility import panic, panicWithCallStack
from ..commonPy import asnParser

g_HeaderFile = None  # type: IO[Any]
g_SourceFile = None  # type: IO[Any]
g_GnuplotFile = None  # type: IO[Any]

g_MyEvents = None
g_MyCreation = None
g_MyClickPrototypes = None
g_MyAction = None
g_MyControls = None
g_MyLoad = None
g_MySave = None
g_MyThreadsInc = None
g_MyThreadsH = None
g_MyTelemetryActions = None

g_bStarted = False
g_IDs = 20000
g_asn_name = ""
g_outputDir = ""
g_maybeFVname = ""
g_perFV = set()  # type: Set[str]
g_langPerSP = {}


def CleanName(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def WriteSourceFileStart():
    g_SourceFile.write('''#include "wx/wxprec.h"
#include "wx/convauto.h"

#ifdef __BORLANDC__
#pragma hdrstop
#endif

#ifndef WX_PRECOMP
#include "wx/wx.h"
#endif

#include "telecmds.h"

#include <iostream>
#include <sstream>
#include <iomanip>

#include <mqueue.h>

#include "debug_messages.h"
#include "queue_manager.h"

IMPLEMENT_DYNAMIC_CLASS( TeleCmds, wxFrame )

BEGIN_EVENT_TABLE( TeleCmds, wxFrame )
#include "MyEvents.inc"
END_EVENT_TABLE()

using namespace std;

template <class T>
bool StringToAny(const char *controlName, const std::string& s, T& result, string& msgError)
{
    if (s.length() == 0) {
        msgError = string(controlName) + string(" is empty!");
        return false;
    }
    std::istringstream str(s);
    str >> result;
    if (str.bad() || !str.eof()) {
        std::ostringstream ostr;
        ostr << "Couldn't convert '" << s << "' to " << controlName << " !\\n";
        msgError = ostr.str();
        return false;
    }
    return true;
};

TeleCmds::TeleCmds()
{
    Init();
}

TeleCmds::TeleCmds( wxWindow* parent, wxWindowID id, const wxString& caption, const wxPoint& pos, const wxSize& size, long style )
{
    Init();
    Create(parent, id, caption, pos, size, style);
}

bool TeleCmds::Create( wxWindow* parent, wxWindowID id, const wxString& caption, const wxPoint& pos, const wxSize& size, long style )
{
    wxFrame::Create( parent, id, caption, pos, size, style );

    CreateControls();
    Centre();
    return true;
}

TeleCmds::~TeleCmds()
{
}

void TeleCmds::Init()
{
}

bool TeleCmds::ShowToolTips()
{
    return true;
}

wxBitmap TeleCmds::GetBitmapResource( const wxString& name )
{
    wxUnusedVar(name);
    return wxNullBitmap;
}

wxIcon TeleCmds::GetIconResource( const wxString& name )
{
    wxUnusedVar(name);
    return wxNullIcon;
}

#include "MyThreads.h"
#include "MyThreads.inc"

void TeleCmds::CreateControls()
{
    TeleCmds* itemDialog1 = this;

    wxBoxSizer* itemBoxSizer2 = new wxBoxSizer(wxVERTICAL);
    itemDialog1->SetSizer(itemBoxSizer2);

    _itemNotebook3 = new wxNotebook( itemDialog1, ID_NOTEBOOK, wxDefaultPosition, wxSize(400, 300), wxNB_DEFAULT );

#include "MyCreation.inc"

    itemBoxSizer2->Add(_itemNotebook3, 1, wxGROW|wxALL, 5);
}

''')

enumFieldNames = {}  # type: Dict[str, int]


def VerifySingleFieldEnums(node):
    names = asnParser.g_names
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnBasicNode):
        pass
    elif isinstance(node, AsnEnumerated):
        for m in node._members:
            if m[0] not in enumFieldNames or enumFieldNames[m[0]] == id(node):
                enumFieldNames[m[0]] = id(node)
            else:  # pragma: no cover
                panic("ENUMERATED fields must be unique (across all ENUMERATED) for the GUI mapper to work... (%s)" % node.Location())  # pragma: no cover
    elif isinstance(node, AsnSequence) or isinstance(node, AsnSet) or isinstance(node, AsnChoice):
        for x in node._members:
            VerifySingleFieldEnums(x[1])
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        VerifySingleFieldEnums(node._containedType)
    elif isinstance(node, AsnMetaMember):
        VerifySingleFieldEnums(names[node._containedType])
    else:  # pragma: no cover
        panicWithCallStack("unsupported %s (%s)" % (str(node.__class__), node.Location()))  # pragma: no cover


def OneTimeOnly(unused_modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, unused_useOSS):
    for typename in asnParser.g_names:
        node = asnParser.g_names[typename]
        VerifySingleFieldEnums(node)

    global g_outputDir
    g_outputDir = outputDir
    global g_maybeFVname
    g_maybeFVname = maybeFVname
    global g_HeaderFile
    g_HeaderFile = open(outputDir + 'telecmds.h', 'w')
    global g_GnuplotFile
    g_GnuplotFile = open(outputDir + 'gnuplot', 'w')
    g_HeaderFile.write('''#ifndef __TELECMDS_H__
#define __TELECMDS_H__

#include "wx/notebook.h"

#define ID_TELECMDS 10001
#define ID_NOTEBOOK 10005
#define SYMBOL_TELECMDS_IDNAME ID_TELECMDS
#define SYMBOL_TELECMDS_TITLE _T("TeleCommands")
#define SYMBOL_TELECMDS_SIZE wxSize(800, 600)
#define SYMBOL_TELECMDS_POSITION wxDefaultPosition
#define SYMBOL_TELECMDS_STYLE wxCAPTION|wxRESIZE_BORDER|wxSYSTEM_MENU|wxCLOSE_BOX|wxDIALOG_MODAL|wxTAB_TRAVERSAL
''')
    global g_IDs
    g_HeaderFile.write("#define ID_MENU_RI " + str(g_IDs) + "\n")
    g_IDs += 1
    g_HeaderFile.write("#define ID_MENU_SAVE " + str(g_IDs) + "\n")
    g_IDs += 1
    g_HeaderFile.write("#define ID_MENU_LOAD " + str(g_IDs) + "\n")
    g_IDs += 1
    g_HeaderFile.write("#define ID_MENU_ABOUT " + str(g_IDs) + "\n")
    g_IDs += 1
    g_HeaderFile.write("#define ID_MENU_QUIT " + str(g_IDs) + "\n")
    g_IDs += 1
    g_HeaderFile.write("\n")
    g_HeaderFile.write('''
class TeleCmds : public wxFrame
{
    DECLARE_DYNAMIC_CLASS( TeleCmds )
    DECLARE_EVENT_TABLE()
public:
    TeleCmds();
    TeleCmds( wxWindow* parent, wxWindowID id = SYMBOL_TELECMDS_IDNAME, const wxString& caption = SYMBOL_TELECMDS_TITLE, const wxPoint& pos = SYMBOL_TELECMDS_POSITION, const wxSize& size = SYMBOL_TELECMDS_SIZE, long style = SYMBOL_TELECMDS_STYLE );

    bool Create( wxWindow* parent, wxWindowID id = SYMBOL_TELECMDS_IDNAME, const wxString& caption = SYMBOL_TELECMDS_TITLE, const wxPoint& pos = SYMBOL_TELECMDS_POSITION, const wxSize& size = SYMBOL_TELECMDS_SIZE, long style = SYMBOL_TELECMDS_STYLE );
    ~TeleCmds();
    void Init();
    void CreateControls();

#include "MyClickPrototypes.inc"
    wxBitmap GetBitmapResource( const wxString& name );
    wxIcon GetIconResource( const wxString& name );
    static bool ShowToolTips();

    wxNotebook* _itemNotebook3;
''')
    g_HeaderFile.write('''
#include "MyControls.inc"
};
''')
    global g_MyEvents
    g_MyEvents = open(outputDir + "MyEvents.inc", "w")
    global g_MyCreation
    g_MyCreation = open(outputDir + "MyCreation.inc", "w")
    global g_MyClickPrototypes
    g_MyClickPrototypes = open(outputDir + "MyClickPrototypes.inc", "w")
    global g_MyControls
    g_MyControls = open(outputDir + "MyControls.inc", "w")
    global g_MyLoad
    g_MyLoad = open(g_outputDir + 'MyLoad.inc', 'w')
    global g_MySave
    g_MySave = open(g_outputDir + 'MySave.inc', 'w')
    global g_MyThreadsInc
    g_MyThreadsInc = open(g_outputDir + 'MyThreads.inc', 'w')
    global g_MyThreadsH
    g_MyThreadsH = open(g_outputDir + 'MyThreads.h', 'w')
    global g_MyTelemetryActions
    g_MyTelemetryActions = open(g_outputDir + "MyTelemetryActions.inc", 'w')
    global g_SourceFile
    g_SourceFile = open(outputDir + 'telecmds.cpp', 'w')
    global g_asn_name
    g_asn_name = os.path.basename(os.path.splitext(asnFile)[0])
    g_SourceFile.write("#include \"%s.h\"\n\n" % g_asn_name)
    g_SourceFile.write("#include \"%s_enums_def.h\"\n" % maybeFVname)
    WriteSourceFileStart()
    g_SourceFile.write("\n")
    if maybeFVname == "":
        panic("GUI APLCs must have an FV_Name attribute! (%s)\n" % subProgram._id + "." + subProgramImplementation)  # pragma: no cover
    g_SourceFile.write("#include \"%s_gui_header.h\"\n\n" % maybeFVname)
    g_SourceFile.write("#include \"queue_manager.h\"\n\n")
    g_SourceFile.write("void TeleCmds::OnMenu_Click( wxCommandEvent& event )\n{\n")
    g_SourceFile.write("#include \"MyActions.inc\"\n")
    g_SourceFile.write("}\n\n")
    g_SourceFile.write("void TeleCmds::OnMenu_Save( wxCommandEvent& event )\n{\n")
    g_SourceFile.write("#include \"MySave.inc\"\n")
    g_SourceFile.write("}\n\n")
    g_SourceFile.write("void TeleCmds::OnMenu_Load( wxCommandEvent& event )\n{\n")
    g_SourceFile.write("#include \"MyLoad.inc\"\n")
    g_SourceFile.write("}\n\n")
    g_SourceFile.write("void TeleCmds::OnMenu_About( wxCommandEvent& event )\n{\n")
    g_SourceFile.write("    wxMessageBox(_T(\"This Graphical User Interface (GUI) was automatically created\\nby code generators developed\\nfor the European Space Agency (ESA)\\nby Semantix Information Technologies\\n\\n(C) Semantix Information Technologies 2008\"), _T(\"About Auto-GUI\"), wxICON_INFORMATION);\n")
    g_SourceFile.write("}\n\n")
    g_SourceFile.write("void TeleCmds::OnMenu_Quit( wxCommandEvent& event )\n{\n")
    g_SourceFile.write("    Close(TRUE);\n    exit(0);\n")
    g_SourceFile.write("}\n\n")

    # Prototypes in the class declaration
    g_MyClickPrototypes.write("void OnMenu_Click( wxCommandEvent& event );\n")
    g_MyClickPrototypes.write("void OnMenu_Save( wxCommandEvent& event );\n")
    g_MyClickPrototypes.write("void OnMenu_Load( wxCommandEvent& event );\n")
    g_MyClickPrototypes.write("void OnMenu_About( wxCommandEvent& event );\n")
    g_MyClickPrototypes.write("void OnMenu_Quit( wxCommandEvent& event );\n")

    g_MyCreation.write("wxMenu *menuFile = new wxMenu;\n")
    g_MyCreation.write("menuFile->Append( ID_MENU_LOAD, _T(\"&Load...\") );\n")
    g_MyCreation.write("menuFile->Append( ID_MENU_SAVE, _T(\"&Save as...\") );\n")
    g_MyCreation.write("menuFile->AppendSeparator();\n")
    g_MyCreation.write("menuFile->Append( ID_MENU_ABOUT, _T(\"&About...\") );\n")
    g_MyCreation.write("menuFile->AppendSeparator();\n")
    g_MyCreation.write("menuFile->Append( ID_MENU_QUIT, _T(\"E&xit\") );\n")

    g_MyCreation.write("wxMenu *menuFileRI = new wxMenu;\n")
    g_MyCreation.write("menuFileRI->Append( ID_MENU_RI, _T(\"&Invoke current RI\") );\n")

    g_MyCreation.write("wxMenuBar *menuBar = new wxMenuBar;\n")
    g_MyCreation.write("menuBar->Append( menuFile, _T(\"&File\") );\n")
    g_MyCreation.write("menuBar->Append( menuFileRI, _T(\"&Invoke RIs\") );\n")

    g_MyCreation.write("SetMenuBar( menuBar );\n")

    # Instructions for actions per RI
    global g_MyAction
    g_MyAction = open(outputDir + "MyActions.inc", "w")

    g_MyThreadsH.write("#ifndef __MYTHREADSH__\n")
    g_MyThreadsH.write("#define __MYTHREADSH__\n\n")
    g_MyThreadsH.write("#include \"wx/thread.h\"\n\n")
    g_MyThreadsH.write("#include \"PrintTypesAsASN1.h\"\n\n")


# Called once per RI (i.e. per SUBPROGRAM IMPLEMENTATION)
def OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS):
    # print modelingLanguage, subProgram, subProgramImplementation, maybeFVname
    g_langPerSP[subProgram] = modelingLanguage
    global g_bStarted
    if not g_bStarted:
        g_bStarted = True
        OneTimeOnly(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS)
    global g_IDs
    CleanSP = CleanName(subProgram._id)
    g_HeaderFile.write("#define ID_SCROLWND_" + CleanSP + " " + str(g_IDs) + "\n")
    g_IDs += 1
    g_MyEvents.write("    EVT_MENU( ID_MENU_RI, TeleCmds::OnMenu_Click )\n")
    g_MyEvents.write("    EVT_MENU( ID_MENU_LOAD, TeleCmds::OnMenu_Load )\n")
    g_MyEvents.write("    EVT_MENU( ID_MENU_SAVE, TeleCmds::OnMenu_Save )\n")
    g_MyEvents.write("    EVT_MENU( ID_MENU_ABOUT, TeleCmds::OnMenu_About )\n")
    g_MyEvents.write("    EVT_MENU( ID_MENU_QUIT, TeleCmds::OnMenu_Quit )\n")

    # Instructions to create the dialog
    g_MyControls.write("wxScrolledWindow* _itemScrolledWindow_%s;\n" % CleanSP)
    g_MyCreation.write("_itemScrolledWindow_%s = new wxScrolledWindow( _itemNotebook3, ID_SCROLWND_%s, wxDefaultPosition, wxSize(100, 100), wxSUNKEN_BORDER|wxHSCROLL|wxVSCROLL|wxALWAYS_SHOW_SB );\n" % (CleanSP, CleanSP))
    g_MyCreation.write("_itemScrolledWindow_%s->SetScrollbars(1, 1, 0, 0);\n" % CleanSP)
    g_MyCreation.write("wxBoxSizer* itemBoxSizer_%s = new wxBoxSizer(wxVERTICAL);\n" % CleanSP)
    g_MyCreation.write("_itemScrolledWindow_%s->SetSizer(itemBoxSizer_%s);\n\n" %
                       (CleanSP, CleanSP))
#
# deprecated, using buttons
#
#    g_MyCreation.write("wxBoxSizer* itemBoxSizerButtons_%s = new wxBoxSizer(wxHORIZONTAL);\n" % CleanSP)
#    g_MyCreation.write("itemBoxSizer_%s->Add(itemBoxSizerButtons_%s, 0, wxALIGN_CENTER_HORIZONTAL|wxALL, 5);\n" %
#       (CleanSP, CleanSP))
#
#    g_MyCreation.write("wxButton* itemButton_ri_%s = new wxButton( _itemScrolledWindow_%s, ID_BTN_RI_%s, _(\"Invoke %s\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
#       (CleanSP, CleanSP, CleanSP, CleanSP ))
#    g_MyCreation.write("wxButton* itemButton_save_%s = new wxButton( _itemScrolledWindow_%s, ID_BTN_SAVE_%s, _(\"Save...\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
#       (CleanSP, CleanSP, CleanSP ))
#    g_MyCreation.write("wxButton* itemButton_load_%s = new wxButton( _itemScrolledWindow_%s, ID_BTN_LOAD_%s, _(\"Load...\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
#       (CleanSP, CleanSP, CleanSP ))
#    g_MyCreation.write("wxButton* itemButton_quit_%s = new wxButton( _itemScrolledWindow_%s, ID_BTN_QUIT_%s, _(\"Quit\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
#       (CleanSP, CleanSP, CleanSP ))
#    g_MyCreation.write("itemBoxSizerButtons_%s->Add(itemButton_ri_%s, 0, wxALIGN_LEFT|wxALL, 5);\n\n" % (CleanSP, CleanSP))
#    g_MyCreation.write("itemBoxSizerButtons_%s->Add(itemButton_save_%s, 0, wxALIGN_CENTER_HORIZONTAL|wxALL, 5);\n\n" % (CleanSP, CleanSP))
#    g_MyCreation.write("itemBoxSizerButtons_%s->Add(itemButton_load_%s, 0, wxALIGN_RIGHT|wxALL, 5);\n\n" % (CleanSP, CleanSP))
#    g_MyCreation.write("itemBoxSizerButtons_%s->Add(itemButton_quit_%s, 0, wxALIGN_RIGHT|wxALL, 5);\n\n" % (CleanSP, CleanSP))

    # have we ever seen before the combination of FVname and Language?
    if maybeFVname + modelingLanguage.lower() not in g_perFV:
        # No, check for things that must be instantiated once per FV+Lang
        g_perFV.add(maybeFVname + modelingLanguage.lower())

        # The first time you see an FV with an sp_impl that is also a GUI_PI, create a thread to poll /FVName_PI_queue
        if modelingLanguage.lower() == "gui_pi":
            # We have telemetry, we need a thread polling the /xyz_PI_queue (xyz: g_maybeFVname)
            cleanFVname = CleanName(g_maybeFVname)
            # g_MyThreadsH.write("#include \"%s_GUI_reader.h\"\n" % cleanFVname)
            g_MyThreadsH.write("class %s_telemetry : public wxThread {\n" % cleanFVname)
            g_MyThreadsH.write("public:\n")
            g_MyThreadsH.write("    %s_telemetry(TeleCmds *);\n" % cleanFVname)
            g_MyThreadsH.write("    virtual void *Entry();\n")
            g_MyThreadsH.write("    virtual void OnExit();\n")
            g_MyThreadsH.write("private:\n")
            g_MyThreadsH.write("    mqd_t _queue_id;\n")
            g_MyThreadsH.write("    char QName[1024];\n")
            g_MyThreadsH.write("    TeleCmds *_pFrame;\n")
            # g_MyThreadsH.write("    int _queue_was_bad;\n")
            g_MyThreadsH.write("};\n\n")
            g_MyThreadsInc.write("%s_telemetry::%s_telemetry(TeleCmds *pFrame)\n{\n" % (cleanFVname, cleanFVname))
            g_MyThreadsInc.write("    _queue_id = (mqd_t)-1;\n")
            g_MyThreadsInc.write("    _pFrame = pFrame;\n")
            g_MyThreadsInc.write("    sprintf(QName, \"%%d_%s_PI_queue\", geteuid());\n" % g_maybeFVname)
            g_MyThreadsInc.write("    if (0 != open_exchange_queue_for_reading((char*)QName, &_queue_id)) {\n")
            g_MyThreadsInc.write("        cerr << \"Failed to open communication channel with ASSERT binary\" << endl;\n")
            g_MyThreadsInc.write("        exit(1);\n")
            g_MyThreadsInc.write("    }\n")
            # g_MyThreadsInc.write("    _queue_was_bad = GUI_%s_reader_initialize();\n" % cleanFVname)
            g_MyThreadsInc.write("}\n\n")
            g_MyThreadsInc.write("void *%s_telemetry::Entry()\n{\n" % cleanFVname)
            g_MyThreadsInc.write("    if (_queue_id == (mqd_t)-1) { cout << \"queue \" << QName << \" does not exist!\\n\"; return NULL; }\n")
            # g_MyThreadsInc.write("    if (_queue_was_bad) { cout << \"queue for %s does not exist!\\n\"; return NULL; }\n" % g_maybeFVname)
            g_MyThreadsInc.write("    struct mq_attr mqstat;\n")
            g_MyThreadsInc.write("    mq_getattr(_queue_id, &mqstat);\n")
            g_MyThreadsInc.write("    void* message_data_received = malloc(mqstat.mq_msgsize);\n")
            g_MyThreadsInc.write("    int message_received_type = -1;\n")
            g_MyThreadsInc.write("    if (!message_data_received) { cout << \"Out of memory in queue Entry\\n\"; }\n")
            g_MyThreadsInc.write("    while(1) {\n")
            g_MyThreadsInc.write("        if (TestDestroy()) break;\n")
            g_MyThreadsInc.write("        message_received_type = -1;\n")
            # g_MyThreadsInc.write("        GUI_%s_read_data();\n" % cleanFVname)
            g_MyThreadsInc.write("        retrieve_message_from_queue(_queue_id, mqstat.mq_msgsize, message_data_received, &message_received_type);\n")
            g_MyThreadsInc.write("        if (message_received_type != -1) {\n")
            g_MyThreadsInc.write("            //cout << \"Received telemetry of type\" << message_received_type << endl;\n")
            g_MyThreadsInc.write("            switch(message_received_type) {\n")
            g_MyThreadsInc.write("#include \"MyTelemetryActions.inc\"\n")
            g_MyThreadsInc.write("            }\n")
            g_MyThreadsInc.write("        }\n")
            g_MyThreadsInc.write("        wxThread::Sleep(10);\n")
            g_MyThreadsInc.write("    }\n")
            g_MyThreadsInc.write("    return NULL;\n")
            g_MyThreadsInc.write("}\n\n")
            g_MyThreadsInc.write("void %s_telemetry::OnExit()\n{\n" % cleanFVname)
            g_MyThreadsInc.write("}\n\n")
            g_MyCreation.write("wxThread *p_%s = new %s_telemetry(this);\n" % (cleanFVname, cleanFVname))
            g_MyCreation.write("p_%s->Create();\n" % cleanFVname)
            g_MyCreation.write("p_%s->Run();\n" % cleanFVname)

    g_MyCreation.write("_itemScrolledWindow_%s->FitInside();\n" % CleanSP)
    if modelingLanguage.lower() == "gui_pi":
        g_MyCreation.write("_itemNotebook3->AddPage(_itemScrolledWindow_%s, _(\"%s\\n(telemetry)\"));\n\n" %
                           (CleanSP, CleanSP))
    elif modelingLanguage.lower() == "gui_ri":
        g_MyCreation.write("_itemNotebook3->AddPage(_itemScrolledWindow_%s, _(\"%s\\n(telecommand)\"));\n\n" %
                           (CleanSP, CleanSP))

    if modelingLanguage.lower() == "gui_pi":
        g_MyTelemetryActions.write("            case i_%s:\n" % CleanSP)
        g_MyTelemetryActions.write("            {\n")
        g_MyTelemetryActions.write('                long long arrivalTime = getTimeInMilliseconds();\n')
        g_MyTelemetryActions.write("                wxMutexGuiEnter();\n")
        g_MyTelemetryActions.write("                char *pData = (char *)message_data_received;\n")
        names = asnParser.g_names
        leafTypeDict = asnParser.g_leafTypeDict
        for param in subProgram._params:
            node = names[param._signal._asnNodename]
            CleanParam = CleanName(param._id)
            CleanASNType = CleanName(param._signal._asnNodename)
            g_MyTelemetryActions.write("                // Read the data for param %s\n" % param._id)
            g_MyTelemetryActions.write("                asn1Scc%s var_%s;\n" % (CleanASNType, CleanParam))
            g_MyTelemetryActions.write("                memcpy(&var_%s, pData, sizeof(var_%s));\n" % (CleanParam, CleanParam))
            g_MyTelemetryActions.write("                pData += sizeof(var_%s);\n" % CleanParam)
            CopyDataFromASN1ToDlg(g_MyTelemetryActions, "_pFrame->", "var_" + CleanParam, "%s_%s" %
                                  (CleanSP, CleanParam), node, leafTypeDict, names)
            g_MyTelemetryActions.write('                PrintASN1%s("TMDATA: %s::%s", &var_%s);\n' %
                                       (CleanASNType, CleanSP, CleanParam, CleanParam))
            g_MyTelemetryActions.write('                printf("\\n");\n')
        g_MyTelemetryActions.write("                wxMutexGuiLeave();\n")
        g_MyTelemetryActions.write('                cout << "TM %s at " << arrivalTime << endl;\n' % CleanSP)
        g_MyTelemetryActions.write("            }\n")
        g_MyTelemetryActions.write("            break;\n")


def WriteCodeForGUIControls(prefix, parentControl, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    global g_IDs
    CleanSP = CleanName(subProgram._id)
    CleanParam = CleanName(param._id)
    ScrollWnd = "_itemScrolledWindow_%s" % CleanSP
    if prefix == "":
        prefix = CleanSP + "::" + CleanParam
    varPrefix = prefix.replace("::", "_")
    txtPrefix = re.sub(r'^.*::', '', prefix)
    # Depending on the type of the node, create the appropriate controls
    if isinstance(node, AsnInt) or isinstance(node, AsnReal) or isinstance(node, AsnOctetString):
        # Write a static label before the child
        g_MyCreation.write("wxStaticText* itemStaticText_%s =  new wxStaticText( %s, wxID_STATIC, _(\"%s\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
                           (varPrefix, ScrollWnd, txtPrefix))
        g_MyCreation.write("%s->Add(itemStaticText_%s, 0, wxALIGN_LEFT|wxALL, 5);\n" %
                           (parentControl, varPrefix))
        # Use a simple edit box
        g_HeaderFile.write("#define ID_TEXTCTRL_%s %s\n" %
                           (varPrefix, g_IDs))
        g_IDs += 1
        g_MyControls.write("wxTextCtrl* _itemTextCtrl_%s;\n" % varPrefix)
        g_MyCreation.write("_itemTextCtrl_%s = new wxTextCtrl( %s, ID_TEXTCTRL_%s, _T(\"\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
                           (varPrefix, ScrollWnd, varPrefix))
        g_MyCreation.write("%s->Add(_itemTextCtrl_%s, 0, wxALIGN_LEFT|wxALL, 5);\n\n" %
                           (parentControl, varPrefix))
    elif isinstance(node, AsnBool):
        # Write a checkbox
        g_HeaderFile.write("#define ID_CHECKBOX_%s %s\n" % (varPrefix, g_IDs))
        g_IDs += 1
        g_MyControls.write("wxCheckBox* _itemCheckBox_%s;\n" % varPrefix)
        g_MyCreation.write("_itemCheckBox_%s = new wxCheckBox( %s, ID_CHECKBOX_%s, _T(\"%s\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
                           (varPrefix, ScrollWnd, varPrefix, txtPrefix))
        g_MyCreation.write("_itemCheckBox_%s->SetValue(false);\n" % varPrefix)
        g_MyCreation.write("%s->Add(_itemCheckBox_%s, 0, wxALIGN_LEFT|wxALL, 5);\n\n" %
                           (parentControl, varPrefix))
    elif isinstance(node, AsnEnumerated):
        # Write a static label before the child
        g_MyCreation.write("wxStaticText* itemStaticText_%s =  new wxStaticText( %s, wxID_STATIC, _T(\"%s\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
                           (varPrefix, ScrollWnd, txtPrefix))
        g_MyCreation.write("%s->Add(itemStaticText_%s, 0, wxALIGN_LEFT|wxALL, 5);\n\n" %
                           (parentControl, varPrefix))
        # Write a combo
        g_MyControls.write("wxArrayString _itemChoiceStrings_%s;\n" % varPrefix)
        for enumOption in node._members:
            g_MyCreation.write("_itemChoiceStrings_%s.Add(_T(\"%s\"));\n" %
                               (varPrefix, enumOption[0]))
        g_HeaderFile.write("#define ID_CHOICE_%s %s\n" % (varPrefix, g_IDs))
        g_IDs += 1
        g_MyControls.write("wxChoice* _itemChoice_%s;\n" % varPrefix)
        g_MyCreation.write("_itemChoice_%s = new wxChoice(%s, ID_CHOICE_%s, wxDefaultPosition, wxDefaultSize, _itemChoiceStrings_%s, 0);\n" %
                           (varPrefix, ScrollWnd, varPrefix, varPrefix))
        g_MyCreation.write("%s->Add(_itemChoice_%s, 0, wxALIGN_LEFT|wxALL, 5);\n" %
                           (parentControl, varPrefix))
    elif isinstance(node, AsnSequence) or isinstance(node, AsnChoice) or isinstance(node, AsnSet):
        # Recurse on the children, but first place them all inside a StaticBoxSizer
        g_MyCreation.write("wxStaticBox* itemStaticBoxSizer_%s_Static = new wxStaticBox(%s, wxID_ANY, _T(\"%s\"));\n" %
                           (varPrefix, ScrollWnd, txtPrefix))
        g_MyControls.write("wxStaticBoxSizer* _itemStaticBoxSizer_%s;\n" % varPrefix)
        g_MyCreation.write("_itemStaticBoxSizer_%s = new wxStaticBoxSizer(itemStaticBoxSizer_%s_Static, wxVERTICAL);\n" %
                           (varPrefix, varPrefix))
        g_MyCreation.write("%s->Add(_itemStaticBoxSizer_%s, 0, wxALIGN_LEFT|wxALL, 5);\n\n" %
                           (parentControl, varPrefix))
        # If it is a CHOICE, we must allow one to specify which child, so write a combo
        if isinstance(node, AsnChoice):
            g_MyControls.write("wxArrayString _itemChoiceStrings_%s;\n" % varPrefix)
            for child in node._members:
                g_MyCreation.write("_itemChoiceStrings_%s.Add(_T(\"%s\"));\n" %
                                   (varPrefix, child[0]))
            g_HeaderFile.write("#define ID_CHOICE_%s %s\n" % (varPrefix, g_IDs))
            g_IDs += 1
            g_MyEvents.write("    EVT_CHOICE( ID_CHOICE_" + varPrefix + ", TeleCmds::UpdateChoice_" + varPrefix + " )\n")
            g_MyControls.write("wxChoice* _itemChoice_%s;\n" % varPrefix)
            g_MyCreation.write("_itemChoice_%s = new wxChoice(%s, ID_CHOICE_%s, wxDefaultPosition, wxDefaultSize, _itemChoiceStrings_%s, 0);\n" %
                               (varPrefix, ScrollWnd, varPrefix, varPrefix))
            g_MyCreation.write("%s->Add(_itemChoice_%s, 0, wxALIGN_LEFT|wxALL, 5);\n" %
                               ("_itemStaticBoxSizer_%s" % varPrefix, varPrefix))
        # Recurse on a children
        g_MyCreation.write("// Children of " + str(node) + "\n\n")
        for child in node._members:
            CleanChild = CleanName(child[0])
            g_MyCreation.write("// Child " + child[0] + "\n")
            childType = child[1]
            if isinstance(childType, AsnMetaMember):
                childType = names[childType._containedType]
            control = "_itemStaticBoxSizer_%s" % varPrefix
            WriteCodeForGUIControls(prefix + "::" + CleanChild, control, childType, subProgram, subProgramImplementation, param, leafTypeDict, names)
        if isinstance(node, AsnChoice):
            g_MyCreation.write("wxCommandEvent dum_%s; UpdateChoice_%s(dum_%s);\n" % (varPrefix, varPrefix, varPrefix))
            g_MyClickPrototypes.write("void UpdateChoice_%s(wxCommandEvent& event);\n" % varPrefix)
            g_SourceFile.write("void TeleCmds::UpdateChoice_%s(wxCommandEvent& event)\n{\n" % varPrefix)
            count = 0
            for unused_child in node._members:
                g_SourceFile.write("    if (%d == _itemChoice_%s->GetCurrentSelection()) {\n" % (count, varPrefix))
                g_SourceFile.write("        _itemStaticBoxSizer_%s->Show((size_t)%d);\n" % (varPrefix, count + 1))
                oCount = 0
                for unused_child2 in node._members:
                    if oCount != count:
                        g_SourceFile.write("        _itemStaticBoxSizer_%s->Show((size_t)%d);\n" % (varPrefix, oCount + 1))
                    oCount += 1
                g_SourceFile.write("    }\n")
                count += 1
            g_SourceFile.write("    _itemScrolledWindow_%s->FitInside();\n" % CleanSP)
            g_SourceFile.write("}\n\n")
        g_MyCreation.write("// End of SEQUENCE/CHOICE\n\n")
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        # Inside a StaticBoxSizer...
        g_MyCreation.write("wxStaticBox* itemStaticBoxSizer_%s_Static = new wxStaticBox(%s, wxID_ANY, _T(\"%s\"));\n" %
                           (varPrefix, ScrollWnd, txtPrefix))
        g_MyControls.write("wxStaticBoxSizer* _itemStaticBoxSizer_%s;\n" % varPrefix)
        g_MyCreation.write("_itemStaticBoxSizer_%s = new wxStaticBoxSizer(itemStaticBoxSizer_%s_Static, wxVERTICAL);\n" %
                           (varPrefix, varPrefix))
        g_MyCreation.write("%s->Add(_itemStaticBoxSizer_%s, 0, wxALIGN_LEFT|wxALL, 5);\n\n" %
                           (parentControl, varPrefix))
        if len(node._range) == 2 and node._range[0] != node._range[1]:
            g_MyCreation.write("wxStaticText* itemStaticTextNoElements_%s =  new wxStaticText( %s, wxID_STATIC, _(\"Number of Elements\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
                               (varPrefix, ScrollWnd))
            g_MyCreation.write("%s->Add(itemStaticTextNoElements_%s, 0, wxALIGN_LEFT|wxALL, 5);\n" %
                               ("_itemStaticBoxSizer_%s" % varPrefix, varPrefix))
            g_MyControls.write("wxTextCtrl* _itemTextCtrl_%s;\n" % varPrefix)
            g_MyCreation.write("_itemTextCtrl_%s = new wxTextCtrl( %s, ID_TEXTCTRL_%s, _T(\"%s\"), wxDefaultPosition, wxDefaultSize, 0 );\n" %
                               (varPrefix, ScrollWnd, varPrefix, str(node._range[0])))
            g_MyCreation.write("%s->Add(_itemTextCtrl_%s, 0, wxALIGN_LEFT|wxALL, 5);\n\n" %
                               ("_itemStaticBoxSizer_%s" % varPrefix, varPrefix))
            g_HeaderFile.write("#define ID_TEXTCTRL_%s %s\n" % (varPrefix, g_IDs))
            g_IDs += 1
        # output controls for each element
        containedNode = node._containedType
        while isinstance(containedNode, str):
            containedNode = names[containedNode]
        control = "_itemStaticBoxSizer_%s" % varPrefix
        for i in range(0, node._range[-1]):
            WriteCodeForGUIControls(
                prefix + "::Elem_" + ("%02d" % i),
                control, containedNode, subProgram, subProgramImplementation, param, leafTypeDict, names)
    else:  # pragma: no cover
        panic("GUI codegen doesn't support this type yet (%s)" % str(node))  # pragma: no cover


def maybeElseZero(childNo):
    if childNo == 0:
        return ""
    else:
        return "else "


def CopyDataFromDlgToASN1(f, srcVar, destVar, node, leafTypeDict, names):
    if isinstance(node, AsnInt) or isinstance(node, AsnReal):
        targetType = {"INTEGER": "asn1SccSint", "REAL": "double"}[node._leafType]
        f.write("if (false == StringToAny<%s>(\"%s\", _itemTextCtrl_%s->GetValue().ToAscii().release(), %s, msgError)) {\n" % (targetType, srcVar, srcVar, destVar))
        f.write("    wxMessageBox(wxConvLocal.cMB2WC(msgError.c_str()), _T(\"Data input error\"), wxICON_ERROR);\n")
        f.write("    _itemTextCtrl_%s->SetFocus();\n" % srcVar)
        f.write("    return;\n")
        f.write("}\n")
    elif isinstance(node, AsnOctetString):
        f.write("{\n")
        control = "_itemTextCtrl_" + srcVar + "->GetValue()"
        f.write("    for(size_t i=0; i<" + control + ".size(); i++)\n")
        f.write("        " + destVar + ".arr[i] = " + control + ".at(i);\n")
        if isSequenceVariable(node):
            f.write("    " + destVar + ".nCount =  _itemTextCtrl_" + srcVar + "->GetValue().size();\n")
        f.write("}\n")
    elif isinstance(node, AsnBool):
        f.write(destVar + " = (asn1SccUint) (_itemCheckBox_" + srcVar + "->Get3StateValue() == wxCHK_CHECKED);\n")
    elif isinstance(node, AsnEnumerated):
        enumNo = 0
        for enumOption in node._members:
            f.write(("%sif (_itemChoice_" % maybeElseZero(enumNo)) + srcVar + "->GetCurrentSelection() == " + str(enumNo) + ") {\n")
            f.write("    " + destVar + " = ENUM_asn1Scc" + CleanName(enumOption[0]) + ";\n")
            f.write("}\n")
            enumNo += 1
    elif isinstance(node, AsnSequence) or isinstance(node, AsnSet):
        for child in node._members:
            CleanChild = CleanName(child[0])
            childType = child[1]
            if isinstance(childType, AsnMetaMember):
                childType = names[childType._containedType]
            CopyDataFromDlgToASN1(f, srcVar + "_" + CleanChild, destVar + "." + CleanChild, childType, leafTypeDict, names)
    elif isinstance(node, AsnChoice):
        childNo = 0
        for child in node._members:
            CleanChild = CleanName(child[0])
            childType = child[1]
            f.write(("%sif (%d == _itemChoice_" % (maybeElseZero(childNo), childNo)) + srcVar + "->GetCurrentSelection()) {\n")
            if isinstance(childType, AsnMetaMember):
                childType = names[childType._containedType]
            CopyDataFromDlgToASN1(f, srcVar + "_" + CleanChild, destVar + ".u." + CleanChild, childType, leafTypeDict, names)
            f.write("    " + destVar + ".kind = CHOICE_" + child[2] + ";\n")
            f.write("}\n")
            childNo += 1
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        containedNode = node._containedType
        while isinstance(containedNode, str):
            containedNode = names[containedNode]
        if isSequenceVariable(node):
            # Read the number of elements from the edit box
            f.write("if (false == StringToAny<long>(\"%s\", _itemTextCtrl_%s->GetValue().ToAscii().release(), %s.nCount, msgError)) {\n" % (srcVar, srcVar, destVar))
            f.write("    wxMessageBox(wxConvLocal.cMB2WC(msgError.c_str()), _T(\"Data input error\"), wxICON_ERROR);\n")
            f.write("    _itemTextCtrl_%s->SetFocus();\n" % srcVar)
            f.write("    return;\n")
            f.write("}\n")
        # No nCount anymore!
        # else:
        #     f.write(destVar + ".nCount = %s;\n" % str(node._range[-1]))
        for i in range(0, node._range[-1]):
            if isSequenceVariable(node):
                f.write("if (" + destVar + ".nCount>" + str(i) + ") {\n")
            CopyDataFromDlgToASN1(f, srcVar + "_Elem_" + ("%02d" % i), destVar + ".arr[" + str(i) + "]", containedNode, leafTypeDict, names)
            if isSequenceVariable(node):
                f.write("}\n")


def CopyDataFromASN1ToDlg(fDesc, prefix, srcVar, destVar, node, leafTypeDict, names, bClear=False):
    if isinstance(node, AsnInt):
        fDesc.write("{\n")
        fDesc.write("    ostringstream s;\n")
        fDesc.write("    s << " + srcVar + ";\n")
        if not bClear:
            fDesc.write("    %s_itemTextCtrl_%s->SetValue(wxString(wxConvLocal.cMB2WC(s.str().c_str())));\n" % (prefix, destVar))
        else:
            fDesc.write("    %s_itemTextCtrl_%s->SetValue(wxString(wxConvLocal.cMB2WC(\"\")));\n" % (prefix, destVar))
        fDesc.write("}\n")
    elif isinstance(node, AsnReal):
        fDesc.write("{\n")
        fDesc.write("    ostringstream s;\n")
        fDesc.write("    s << fixed << setprecision(8) <<" + srcVar + ";\n")
        if not bClear:
            fDesc.write("    %s_itemTextCtrl_%s->SetValue(wxString(wxConvLocal.cMB2WC(s.str().c_str())));\n" % (prefix, destVar))
        else:
            fDesc.write("    %s_itemTextCtrl_%s->SetValue(wxString(wxConvLocal.cMB2WC(\"\")));\n" % (prefix, destVar))
        fDesc.write("}\n")
    elif isinstance(node, AsnOctetString):
        control = prefix + "_itemTextCtrl_" + destVar
        limit = sourceSequenceLimit(node, srcVar)
        if not bClear:
            fDesc.write(control + "->SetValue(wxString(wxConvLocal.cMB2WC(string((const char *)" + srcVar + ".arr, " + limit + ").c_str())));\n")
        else:
            fDesc.write(control + "->SetValue(wxString(wxConvLocal.cMB2WC(\"\")));\n")
    elif isinstance(node, AsnBool):
        control = prefix + "_itemCheckBox_" + destVar
        if not bClear:
            fDesc.write(control + "->Set3StateValue(" + srcVar + "?wxCHK_CHECKED:wxCHK_UNCHECKED);\n")
        else:
            fDesc.write(control + "->Set3StateValue(wxCHK_UNCHECKED);\n")
    elif isinstance(node, AsnEnumerated):
        enumNo = 0
        if not bClear:
            for enumOption in node._members:
                fDesc.write(("%sif (" % maybeElseZero(enumNo)) + srcVar + " == ENUM_asn1Scc" + CleanName(enumOption[0]) + ") {\n")
                fDesc.write("    " + prefix + "_itemChoice_" + destVar + "->SetSelection(%d);\n" % enumNo)
                fDesc.write("}\n")
                enumNo += 1
        else:
            fDesc.write("    " + prefix + "_itemChoice_" + destVar + "->SetSelection(0);\n")
    elif isinstance(node, AsnSequence) or isinstance(node, AsnSet):
        for child in node._members:
            CleanChild = CleanName(child[0])
            childType = child[1]
            if isinstance(childType, AsnMetaMember):
                childType = names[childType._containedType]
            CopyDataFromASN1ToDlg(fDesc, prefix, srcVar + "." + CleanChild, destVar + "_" + CleanChild, childType, leafTypeDict, names, bClear)
    elif isinstance(node, AsnChoice):
        childNo = 0
        for child in node._members:
            CleanChild = CleanName(child[0])
            childType = child[1]
            fDesc.write("%sif (%s.kind == CHOICE_%s) {\n" %
                        (maybeElseZero(childNo), srcVar, child[2]))
            fDesc.write("    " + prefix + "_itemChoice_" + destVar + "->SetSelection(%d);\n" % childNo)
            fDesc.write("    wxCommandEvent dum;\n")
            fDesc.write("    %sUpdateChoice_" % prefix + destVar + "(dum);\n")
            if isinstance(childType, AsnMetaMember):
                childType = names[childType._containedType]
            CopyDataFromASN1ToDlg(fDesc, prefix, srcVar + ".u." + CleanChild, destVar + "_" + CleanChild, childType, leafTypeDict, names, bClear)
            fDesc.write("}\n")
            childNo += 1
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        containedNode = node._containedType
        while isinstance(containedNode, str):
            containedNode = names[containedNode]
        # The decoding code has been executed, so the .nCount member is ready...
        for i in range(0, node._range[-1]):
            if isSequenceVariable(node):
                fDesc.write("if (" + str(i) + "<" + srcVar + ".nCount) {\n")
                CopyDataFromASN1ToDlg(fDesc, prefix, srcVar + ".arr[" + str(i) + "]", destVar + "_Elem_" + ("%02d" % i), containedNode, leafTypeDict, names, bClear)
                fDesc.write("} else {\n")
                CopyDataFromASN1ToDlg(fDesc, prefix, srcVar + ".arr[" + str(i) + "]", destVar + "_Elem_" + ("%02d" % i), containedNode, leafTypeDict, names, True)
                fDesc.write("}\n")
            else:
                CopyDataFromASN1ToDlg(fDesc, prefix, srcVar + ".arr[" + str(i) + "]", destVar + "_Elem_" + ("%02d" % i), containedNode, leafTypeDict, names, bClear)
        if isSequenceVariable(node):
            fDesc.write("{\n")
            fDesc.write("    ostringstream s;\n")
            fDesc.write("    s << " + srcVar + ".nCount;\n")
            fDesc.write("    " + prefix + "_itemTextCtrl_%s->SetValue(wxString(wxConvLocal.cMB2WC(s.str().c_str())));\n" % destVar)
            fDesc.write("}\n")


def WriteCodeForSave(nodeTypename, node, subProgram, unused_subProgramImplementation, param, leafTypeDict, names):
    CleanSP = CleanName(subProgram._id)
    CleanParam = CleanName(param._id)
    CopyDataFromDlgToASN1(g_MySave, "%s_%s" % (CleanSP, CleanParam), "var_" + CleanParam, node, leafTypeDict, names)
    g_MySave.write("{\n    int ErrCode;\n")
    g_MySave.write("    if (0 == asn1Scc%s_IsConstraintValid(&var_%s, &ErrCode)) {\n" % (CleanName(nodeTypename), CleanParam))
    g_MySave.write("        string msg(\"ASN.1 Constraints are violated with this message!\\n\");\n")
    g_MySave.write("#include \"ConstraintErrors.inc\"\n")
    g_MySave.write("        wxMessageBox(wxConvLocal.cMB2WC(msg.c_str()), _T(\"Data input error\"), wxICON_ERROR);\n")
    g_MySave.write("    } else {\n")
    g_MySave.write("        wxFileDialog flSave(this, _T(\"Choose a file for parameter %s\"), _T(\"\"), _T(\"\"), _T(\"*.per\"), wxFD_SAVE);\n" % param._id)
    g_MySave.write("        if (flSave.ShowModal() == wxID_OK) {\n")
    g_MySave.write("            int errorCode;\n")
    g_MySave.write("            static BitStream strm;\n\n")
    g_MySave.write("            static unsigned char pBuffer[asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING];\n\n" %
                   CleanName(nodeTypename))
    g_MySave.write("            BitStream_Init(&strm, pBuffer, asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING);\n" %
                   CleanName(nodeTypename))
    g_MySave.write("            if (asn1Scc%s_Encode(&var_%s, &strm, &errorCode, TRUE) == FALSE) {\n" %
                   (CleanName(nodeTypename), CleanParam))
    g_MySave.write('                wxMessageBox(_T("Encoding of %s failed"), _T("Error encoding"), wxICON_ERROR);\n' % nodeTypename)
    g_MySave.write("\t\treturn;\n")
    g_MySave.write("            } else {\n")
    g_MySave.write("                FILE *fp = fopen(flSave.GetPath().ToAscii().release(), \"wb\");\n")
    g_MySave.write("                if(fp) {\n")
    g_MySave.write("                    fwrite(pBuffer, 1, BitStream_GetLength(&strm), fp);\n")
    g_MySave.write("                    fclose(fp);\n")
    g_MySave.write("                } else {\n")
    g_MySave.write("                    wxMessageBox(_T(\"Could not open file for writing...\"), _T(\"Error in saving\"), wxICON_ERROR);\n")
    g_MySave.write("                }\n")
    g_MySave.write("           }\n")
    g_MySave.write("        } else return;\n")
    g_MySave.write("    }\n")
    g_MySave.write("}\n")


def WriteCodeForLoad(nodeTypename, node, subProgram, unused_subProgramImplementation, param, leafTypeDict, names):
    CleanSP = CleanName(subProgram._id)
    CleanParam = CleanName(param._id)
    g_MyLoad.write("    {\n")
    g_MyLoad.write("        wxFileDialog flLoad(this, _T(\"Choose a file for parameter %s\"), _T(\"\"), _T(\"\"), _T(\"*.per\"), wxFD_OPEN);\n" % param._id)
    g_MyLoad.write("        if (flLoad.ShowModal() == wxID_OK) {\n")
    g_MyLoad.write("            int errorCode;\n\n")
    g_MyLoad.write("            static BitStream strm;\n\n")
    g_MyLoad.write("            static unsigned char pBuffer[asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING];\n\n" %
                   CleanName(nodeTypename))
    g_MyLoad.write("            FILE *fp = fopen(flLoad.GetPath().ToAscii().release(), \"rb\");\n")
    g_MyLoad.write("            if (fp) {\n")
    g_MyLoad.write("                int iBufferSize = fread(pBuffer, 1, asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING, fp);\n" %
                   CleanName(nodeTypename))
    g_MyLoad.write("                fclose(fp);\n")
    g_MyLoad.write("                BitStream_AttachBuffer(&strm, pBuffer, iBufferSize);\n\n")
    g_MyLoad.write("                if (asn1Scc%s_Decode(&var_%s, &strm, &errorCode)) {\n" %
                   (CleanName(nodeTypename), CleanParam))
    g_MyLoad.write("                    /* Decoding succeeded */\n")
    CopyDataFromASN1ToDlg(g_MyLoad, "", "var_" + CleanParam, "%s_%s" % (CleanSP, CleanParam), node, leafTypeDict, names)
    g_MyLoad.write("                } else {\n")
    g_MyLoad.write("                    wxMessageBox(_T(\"This file did not contain a %s...\"), _T(\"Error in loading\"), wxICON_ERROR);\n" % nodeTypename)
    g_MyLoad.write("                }\n")
    g_MyLoad.write("            } else {\n")
    g_MyLoad.write("                wxMessageBox(_T(\"Could not open file for reading...\"), _T(\"Error in loading\"), wxICON_ERROR);\n")
    g_MyLoad.write("            }\n")
    g_MyLoad.write("        } else return;\n")
    g_MyLoad.write("    }\n")


def WriteCodeForGnuPlot(prefix, node, subProgram, param, names):
    CleanSP = CleanName(subProgram._id)
    CleanParam = CleanName(param._id)
    if prefix in ("TCDATA: ", "TMDATA: "):
        prefix += CleanSP + "::" + CleanParam
    if isinstance(node, AsnInt) or isinstance(node, AsnReal) or isinstance(node, AsnOctetString):
        g_GnuplotFile.write(prefix + '\n')
    elif isinstance(node, AsnBool):
        pass
    elif isinstance(node, AsnEnumerated):
        pass
    elif isinstance(node, AsnSequence) or isinstance(node, AsnSet):
        for child in node._members:
            CleanChild = CleanName(child[0])
            childType = child[1]
            if isinstance(childType, AsnMetaMember):
                childType = names[childType._containedType]
            WriteCodeForGnuPlot(prefix + "::" + CleanChild, childType, subProgram, param, names)
    elif isinstance(node, AsnChoice):
        for child in node._members:
            CleanChild = CleanName(child[0])
            childType = child[1]
            if isinstance(childType, AsnMetaMember):
                childType = names[childType._containedType]
            WriteCodeForGnuPlot(prefix + "::" + CleanChild, childType, subProgram, param, names)
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        containedNode = node._containedType
        while isinstance(containedNode, str):
            containedNode = names[containedNode]
        for _ in range(0, node._range[-1]):
            WriteCodeForGnuPlot(prefix + "::Elem", containedNode, subProgram, param, names)


def WriteCodeForAction(nodeTypename, node, subProgram, unused_subProgramImplementation, param, leafTypeDict, names):
    CleanSP = CleanName(subProgram._id)
    CleanParam = CleanName(param._id)
    CopyDataFromDlgToASN1(g_MyAction, "%s_%s" % (CleanSP, CleanParam), "var_" + CleanParam, node, leafTypeDict, names)
    g_MyAction.write("{\n    int ErrCode;\n")
    g_MyAction.write("    if (0 == asn1Scc%s_IsConstraintValid(&var_%s, &ErrCode)) {\n" % (CleanName(nodeTypename), CleanParam))
    g_MyAction.write("        string msg(\"ASN.1 Constraints are violated with this message!\\n\");\n")
    g_MyAction.write("#include \"ConstraintErrors.inc\"\n")
    g_MyAction.write("        wxMessageBox(wxConvLocal.cMB2WC(msg.c_str()), _T(\"Data input error\"), wxICON_ERROR);\n")
    g_MyAction.write("    } else {\n")
    g_MyAction.write("        int errorCode;\n")
    g_MyAction.write("        static BitStream strm;\n\n")
    g_MyAction.write("        static unsigned char pBuffer[asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING];\n\n" %
                     CleanName(nodeTypename))
    g_MyAction.write("        BitStream_Init(&strm, pBuffer, asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING);\n" %
                     CleanName(nodeTypename))
    g_MyAction.write("        if (asn1Scc%s_Encode(&var_%s, &strm, &errorCode, TRUE) == FALSE) {\n" %
                     (CleanName(nodeTypename), CleanParam))
    g_MyAction.write('            wxMessageBox(_T("Encoding of %s failed... Contact Semantix"), _T("Error encoding"), wxICON_ERROR);\n' % nodeTypename)
    g_MyAction.write("\t\treturn;\n")
    g_MyAction.write("        } else {\n")
    WriteCodeForGnuPlot("TCDATA: ", node, subProgram, param, names)
    g_MyAction.write('            PrintASN1%s("TCDATA: %s::%s", &var_%s);' % (CleanName(nodeTypename), CleanSP, CleanParam, CleanParam))
    g_MyAction.write('            printf("\\n");\n')
    g_MyAction.write("            T_%s_message data;\n" % CleanSP)
    g_MyAction.write("            data.message_identifier = i_%s;\n" % CleanSP)
    g_MyAction.write("            data.message.%s = var_%s;\n" % (CleanParam, CleanParam))
    g_MyAction.write("            static char QName[1024];\n")
    g_MyAction.write("            sprintf(QName, \"/%%d_%s_RI_queue\", geteuid());\n" % g_maybeFVname)
    g_MyAction.write("            mqd_t q = mq_open(QName, O_RDWR | O_NONBLOCK);\n")
    g_MyAction.write("            if (((mqd_t)-1) == q) {\n")
    g_MyAction.write("                wxMessageBox(_T(\"Failed to write message to queue\"), _T(\"Invoking RI failed...\"), wxICON_ERROR);\n")
    g_MyAction.write("            } else {\n")
    g_MyAction.write("                if (0 != write_message_to_queue(q, sizeof(data.message), &data.message, data.message_identifier)) {\n")
    g_MyAction.write('                    fprintf(stderr, "Sending the TC failed...\\n");\n')
    g_MyAction.write('                } else {\n')
    g_MyAction.write('                     cout << "TC %s at " << getTimeInMilliseconds() << endl;\n' % CleanSP)
    g_MyAction.write('                }\n')
    g_MyAction.write("            }\n")
    g_MyAction.write("        }\n")
    g_MyAction.write("    }\n")
    g_MyAction.write("}\n")

g_SPs = []  # type: List[str]
g_bBraceOpen = False


def Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    control = "itemBoxSizer_%s" % CleanName(subProgram._id)
    WriteCodeForGUIControls('', control, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    global g_bBraceOpen
    if len(g_SPs) == 0 or subProgram._id != g_SPs[-1]:
        if g_bBraceOpen:
            g_MyAction.write("} // %s\n" % g_SPs[-1])
            g_MySave.write("} // %s\n" % g_SPs[-1])
            g_MyLoad.write("} // %s\n" % g_SPs[-1])
            g_bBraceOpen = False
        g_SPs.append(subProgram._id)
        if g_langPerSP[subProgram].lower() == "gui_ri":
            g_MyAction.write("if ((int)_itemNotebook3->GetSelection() == %d) {\n" % (len(g_SPs) - 1))
            g_MyAction.write("    string msgError;\n")
            g_MySave.write("if ((int)_itemNotebook3->GetSelection() == %d) {\n" % (len(g_SPs) - 1))
            g_MySave.write("    string msgError;\n")
            g_MyLoad.write("if ((int)_itemNotebook3->GetSelection() == %d) {\n" % (len(g_SPs) - 1))
            g_MyLoad.write("    string msgError;\n")
            g_bBraceOpen = True

    if g_langPerSP[subProgram].lower() == "gui_ri":
        g_MyAction.write("    asn1Scc%s var_%s;\n" % (CleanName(nodeTypename), CleanName(param._id)))
        g_MySave.write("    asn1Scc%s var_%s;\n" % (CleanName(nodeTypename), CleanName(param._id)))
        g_MyLoad.write("    asn1Scc%s var_%s;\n" % (CleanName(nodeTypename), CleanName(param._id)))
        WriteCodeForAction(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
        WriteCodeForSave(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
        WriteCodeForLoad(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    if g_langPerSP[subProgram].lower() == "gui_pi":
        WriteCodeForGnuPlot("TMDATA: ", node, subProgram, param, names)


def OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnShutdown(unused_modelingLanguage, unused_asnFile, unused_sp, unused_subProgramImplementation, unused_maybeFVname):
    pass


def OnFinal():
    if g_bBraceOpen:
        g_MyAction.write("}\n")
        g_MySave.write("}\n")
        g_MyLoad.write("}\n")
    g_HeaderFile.write("\n#endif\n")
    g_MyThreadsH.write("\n#endif\n")

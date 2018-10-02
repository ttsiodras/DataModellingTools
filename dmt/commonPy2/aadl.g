// vim: set expandtab:

options {
        language=Python;
}

{
    from commonPy.aadlAST import *
    from commonPy.utility import panic
    import commonPy.configMT
    global g_currentPackage
    g_currentPackage = ""
}

class AadlParser extends Parser;
options {
        buildAST=false;
        k=4;
//      codeGenBitsetTestThreshold=999;
        defaultErrorHandler=false;
}

aadl_specification 
 
    :
    (aadl_declaration)+
    EOF
;


aadl_declaration 
 
    :
    ( component_classifier | port_group_type | annex_library | package_spec | property_set )
;


component_classifier 
    :
    ( thread_type |   thread_implementation
    | thread_group_type |   thread_group_implementation
    | system_type |   system_implementation
    | data_type |   data_implementation
    | subprogram_type |   subprogram_implementation
    | process_type |   process_implementation
    | processor_type |   processor_implementation
    | memory_type |   memory_implementation
    | bus_type |   bus_implementation
    | device_type |   device_implementation
    )
;


package_file 
 
    :
    fl:PACKAGE p=package_name 
    (
            (public_part (private_part)?)
    |
            private_part
    )
    END p=package_name sl:SEMI   
    EOF
;


package_spec 
    :
    fl:PACKAGE p=package_name { 
        global g_currentPackage
        g_currentPackage = p
        //print "Currently parsing package", g_currentPackage 
    }
    ( (public_part ( private_part )?) | private_part )
    END pn=package_name sl:SEMI   
;
  
public_part 
    :
    PUBLIC package_items 
;

  
private_part
    :
    PRIVATE package_items 
;

 
package_items 
    :
    ( package_item)+ ( propertyAssociations )?
;


package_item 
 
    :  
    component_classifier | port_group_type | annex_library 
;


package_name returns [ pkgId ]
    :
{
    pkgId = ""
}
    id:IDENT { pkgId = id.getText() } ( DOUBLECOLON id2:IDENT { pkgId += "::" + id2.getText() } )*
;


// note: we recognize none by the appropriate subclause object without content
none_stmt 
    :
    NONE SEMI 
; 


thread_type 
 
    :
    THREAD  id:IDENT {
        //print "Now defining THREAD", id.getText()
        //print threadFeatures
        if not commonPy.configMT.g_bOnlySubprograms:
            sp = ApLevelContainer(id.getText())
            g_apLevelContainers[id.getText()] = sp }
    (EXTENDS unique_type_name )?
    ( threadFeatures=featuresThread {
        if not commonPy.configMT.g_bOnlySubprograms:
            for threadFeature in threadFeatures:
               if threadFeature == None: continue
               if not g_signals.has_key(threadFeature._port._type):
                  // panic("Line %d: Referenced datatype (%s) not defined yet" % \
                  //     (id.getLine(),threadFeature._port._type))
                  signal = threadFeature._port._type
               else:
                  signal = g_signals[threadFeature._port._type]
               if threadFeature._port._direction == "IN":
                  param = InParam(id.getText(), threadFeature._id, signal, threadFeature._port)
               elif threadFeature._port._direction == "OUT":
                  param = OutParam(id.getText(), threadFeature._id, signal, threadFeature._port)
               elif threadFeature._port._direction == "INOUT":
                  param = InOutParam(id.getText(), threadFeature._id, signal, threadFeature._port)
               else:
                  panic("No IN/OUT/INOUT specified!")
               sp.AddParam(param)
    } )?
    ( flow_specs )?
    ( properties=propertyAssociations_no_modes {
        if not commonPy.configMT.g_bOnlySubprograms:
            if properties != None:
                if not g_apLevelContainers.has_key(id.getText()):
                   panic("Line %d: THREAD (%s) must first be declared before it is PROPERTIES-ed"  % (id.getLine(), id.getText()))
                sp = g_apLevelContainers[id.getText()]
                for property in properties:
                   if property._name[-15:].lower() == "source_language":
                       stripQuotes = property._propertyExpressionOrList.replace("\"", "")
                       sp.SetLanguage(stripQuotes)
        } )?
    ( annex_subclause )?
    END eid:IDENT sl:SEMI
;

thread_group_type 

    :
    THREAD GROUP    id:IDENT        
    (EXTENDS unique_type_name )?
    (featuresThreadGroup)?
    ( flow_specs )?
    ( pa=propertyAssociations_no_modes )?
    ( annex_subclause )?
    END eid:IDENT SEMI 
;


process_type 

    :
    PROCESS id:IDENT {
        if not commonPy.configMT.g_bOnlySubprograms:
            sp = ApLevelContainer(id.getText())
            g_apLevelContainers[id.getText()] = sp }
    (EXTENDS  unique_type_name )?
    (processFeatures=featuresProcess {
        if not commonPy.configMT.g_bOnlySubprograms:
            for processFeature in processFeatures:
               if processFeature == None: continue
               if not g_signals.has_key(processFeature._port._type):
                  // panic("Line %d: Referenced datatype (%s) not defined yet" % \
                  //     (id.getLine(),processFeature._port._type))
                  signal = processFeature._port._type
               else:
                  signal = g_signals[processFeature._port._type]
               if processFeature._port._direction == "IN":
                  param = InParam(id.getText(), processFeature._id, signal, processFeature._port)
               elif processFeature._port._direction == "OUT":
                  param = OutParam(id.getText(), processFeature._id, signal, processFeature._port)
               elif processFeature._port._direction == "INOUT":
                  param = InOutParam(id.getText(), processFeature._id, signal, processFeature._port)
               else:
                  panic("No IN/OUT/INOUT specified!")
               sp.AddParam(param)
    } )?
    ( flow_specs )?
    ( properties=propertyAssociations_no_modes {
        if not commonPy.configMT.g_bOnlySubprograms:
            if properties != None:
                if not g_apLevelContainers.has_key(id.getText()):
                   panic("Line %d: PROCESS (%s) must first be declared before it is PROPERTIES-ed"  % (id.getLine(), id.getText()))
                sp = g_apLevelContainers[id.getText()]
                for property in properties:
                   if property._name[-15:].lower() == "source_language":
                       stripQuotes = property._propertyExpressionOrList.replace("\"", "")
                       sp.SetLanguage(stripQuotes)
        } )?
    ( annex_subclause )?
    END eid:IDENT SEMI 
;


system_type 

    :
    SYSTEM  id:IDENT        
    (EXTENDS unique_type_name )?
    (fe=featuresSystem {
        g_systems[id.getText()]=[x._sp for x in fe if x._direction == "OUT"]
        //print "Detected RIs for", id.getText(), g_systems[id.getText()]
    } )?
    (flow_specs )?
    (pa=propertyAssociations_no_modes )?
    (annex_subclause )?
    END eid:IDENT SEMI 
;


subprogram_type 

    :
    SUBPROGRAM id:IDENT {
        //print "Now defining SUBPROGRAM", id.getText()
        //print f
        sp = ApLevelContainer(id.getText())
        g_apLevelContainers[id.getText()] = sp }
    (EXTENDS unique_type_name )?
    (features=featuresSubprogram { 
        for spFeature in features:
           if spFeature == None: continue
           if not g_signals.has_key(spFeature._parameter._type):
              // panic("Line %d: Referenced datatype (%s) not defined yet" % \
              //    (id.getLine(),spFeature._parameter._type))
              signal = spFeature._parameter._type
           else:
              signal = g_signals[spFeature._parameter._type]
           if spFeature._parameter._direction == "IN":
              param = InParam(id.getText(), spFeature._id, signal, spFeature._parameter)
           elif spFeature._parameter._direction == "OUT":
              param = OutParam(id.getText(), spFeature._id, signal, spFeature._parameter)
           elif spFeature._parameter._direction == "INOUT":
              param = InOutParam(id.getText(), spFeature._id, signal, spFeature._parameter)
           else:
              panic("No IN/OUT/INOUT specified!")
           sp.AddParam(param)
    } )?
    ( flow_specs )?
    ( properties=propertyAssociations_no_modes {
        if properties != None:
            if not g_apLevelContainers.has_key(id.getText()):
               panic("Line %d: SUBPROGRAM (%s) must first be declared before it is PROPERTIES-ed"  % (id.getLine(), id.getText()))
            sp = g_apLevelContainers[id.getText()]
            for property in properties:
               if property._name[-15:].lower() == "source_language":
                   stripQuotes = property._propertyExpressionOrList.replace("\"", "")
                   sp.SetLanguage(stripQuotes)
               elif property._name[-10:].lower() == "fpga_modes":
                   stripQuotes = property._propertyExpressionOrList.replace("\"", "")
                   sp.SetFPGAModes(stripQuotes)
    } )?
    ( annex_subclause )?
    END eid:IDENT SEMI 
;


data_type 

    :
    DATA    id:IDENT
    (EXTENDS unique_type_name )?
    (featuresData)?
    ( panms=propertyAssociations_no_modes { 
        //print "Data definition of", id.getText(), panms
        asnFilename = ""
        asnNodename = ""
        asnSize = -1
        for prop in panms:
            if prop._name.lower() == "source_text": asnFilename = prop._propertyExpressionOrList[1:-1]
            elif prop._name.lower() == "type_source_name": asnNodename = prop._propertyExpressionOrList[1:-1]
            elif prop._name.lower() == "source_data_size": 
                try:
                    asnSize = int(prop._propertyExpressionOrList)
                except:
                   panic("Line %d: DATA (%s) must have source_data_size be declared as [0-9]B (not '%s')"  % (id.getLine(), id.getText(), prop._propertyExpressionOrList))
        if asnFilename!="" and asnNodename!="" and asnSize != -1:
            s = Signal(asnFilename, asnNodename, asnSize)
            g_signals[id.getText()] = s
            g_signals[g_currentPackage + "::" + id.getText()] = s
        else:
           panic("Line %d: DATA (%s) must have Source_Text, Type_Source_Name and Source_Data_Size"  % (id.getLine(), id.getText()))
    } )?
    ( annex_subclause )?
    END eid:IDENT SEMI 
;


processor_type 

    :
    PROCESSOR       id:IDENT        
    (EXTENDS unique_type_name )?
    (featuresProcessor)?
    ( flow_specs )?
    ( pa=propertyAssociations_no_modes )?
    ( annex_subclause )?
    END eid:IDENT SEMI 
;


memory_type 

    :
    MEMORY  id:IDENT        
    (EXTENDS unique_type_name )?
    (featuresMemory)?
    ( pa=propertyAssociations_no_modes  )?
    ( annex_subclause  )?
    END eid:IDENT SEMI 
;
 

bus_type 

    :
    BUS id:IDENT        
    (EXTENDS unique_type_name )?
    (featuresBus)?
    ( pa=propertyAssociations_no_modes  )?
    ( annex_subclause  )?
    END eid:IDENT SEMI 
;
 

device_type 

    :
    DEVICE  id:IDENT        
    (EXTENDS unique_type_name )?
    (featuresDevice)?
    ( flow_specs )?
    ( pa=propertyAssociations_no_modes  )?
    ( annex_subclause  )?
    END eid:IDENT SEMI 
;
 

//-------------------------------------------------------------------
//  unique type name must refer to a type
// unqiue implemenation name must refer to an implementation
// classifier reference may be incomplete.
// ClassifierReference is an object that has three fields:
// package name, type name, impl name. Any of them can be null
//---------------------------------------------------------------

unique_type_name 
    :
    ( pid: IDENT DOUBLECOLON )* tid:IDENT 
;


unique_impl_name 
    :
    ( pid: IDENT DOUBLECOLON )* tid:IDENT DOT iid:IDENT 
;


classifier_reference returns [ classifier ]
    :
{
    classifier = None
    ptid = None
}
    (ptid:IDENT DOUBLECOLON )* tid:IDENT { 
         if ptid != None: classifier = ptid.getText() + "::" + tid.getText()
         else: classifier = g_currentPackage + "::" + tid.getText() 
    }
    ( DOT iid:IDENT )?
;

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 4.4 Component Implementations
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ category specific implementation portion
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

common_component_impl returns [ listOfProperties ]
    :
{
    listOfProperties = None
}
    (mode_subclause)?
    ( c=containedPropertyAssociations { listOfProperties = c } )?
    ( annex_subclause  )?
;


thread_implementation 

    :
    THREAD IMPL typeid:IDENT DOT defid:IDENT  {
        if not commonPy.configMT.g_bOnlySubprograms:
            if not g_apLevelContainers.has_key(typeid.getText()):
               panic("Line %d: Thread (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
            sp = g_apLevelContainers[typeid.getText()]
            g_threadImplementations.append([typeid.getText(), defid.getText(), sp._language, ""]) }
    (EXTENDS unique_impl_name )?
    (refinestypeSubclause)?
    (threadSubcomponents )?
    (callsSubclause )?
    (mesh=connectionsSubclause {
        if not commonPy.configMT.g_bOnlySubprograms:
            for conn in mesh:
                if conn._from._portId == None or conn._to._portId == None:
                    continue // One of _from,_to are connection_refinements (unsupported)
                sp = g_apLevelContainers[typeid.getText()]
                sp.AddConnection(conn._from, conn._to) } )?
    (flow_impls)?
    cci=common_component_impl {
        if not commonPy.configMT.g_bOnlySubprograms:
            if cci != None:
                if not g_apLevelContainers.has_key(typeid.getText()):
                    panic("Line %d: THREAD (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
                sp = g_apLevelContainers[typeid.getText()]
                for assoc in cci:
                    if assoc == None: continue
                    if assoc._name[-15:].lower() == "source_language":
                        stripQuotes = assoc._value.replace("\"", "")
                        //sp.SetLanguage(stripQuotes) 
                        g_threadImplementations[-1][2] = stripQuotes
                    if assoc._name[-15:].lower() == "fv_name":
                        stripQuotes = assoc._value.replace("\"", "")
                        //sp.SetLanguage(stripQuotes) 
                        g_threadImplementations[-1][3] = stripQuotes
    }
    END id:IDENT DOT id2:IDENT SEMI
;


thread_group_implementation 

    :
    THREAD GROUP IMPL typeid:IDENT DOT defid:IDENT 
        (EXTENDS unique_impl_name )?
        (refinestypeSubclause)?
        (threadgroupSubcomponents )?
        (cs=connectionsSubclause)?
        (flow_impls)?
        cci=common_component_impl
        END id:IDENT DOT id2:IDENT SEMI
;


process_implementation 

    :
    PROCESS IMPL typeid: IDENT DOT defid: IDENT {
        if not commonPy.configMT.g_bOnlySubprograms:
            if not g_apLevelContainers.has_key(typeid.getText()):
               panic("Line %d: Process (%s) must first be declared before it is implemented"  % (typeid.getLine(), typeid.getText()))
            sp = g_apLevelContainers[typeid.getText()]
            g_processImplementations.append([typeid.getText(), defid.getText(), sp._language, ""]) }
    (EXTENDS  unique_impl_name )?
    (refinestypeSubclause)?
    (processSubcomponents )?
    (mesh=connectionsSubclause {
        if not commonPy.configMT.g_bOnlySubprograms:
            for conn in mesh:
                if conn._from._portId == None or conn._to._portId == None:
                    continue // One of _from,_to are connection_refinements (unsupported)
                sp = g_apLevelContainers[typeid.getText()]
                sp.AddConnection(conn._from, conn._to) } )?
    (flow_impls)?
    cci=common_component_impl {
        if not commonPy.configMT.g_bOnlySubprograms:
            if cci != None:
                if not g_apLevelContainers.has_key(typeid.getText()):
                    panic("Line %d: PROCESS (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
                sp = g_apLevelContainers[typeid.getText()]
                for assoc in cci:
                    if assoc == None: continue
                    if assoc._name[-15:].lower() == "source_language":
                        stripQuotes = assoc._value.replace("\"", "")
                        //sp.SetLanguage(stripQuotes) 
                        g_processImplementations[-1][2] = stripQuotes
                    if assoc._name[-15:].lower() == "fv_name":
                        stripQuotes = assoc._value.replace("\"", "")
                        //sp.SetLanguage(stripQuotes) 
                        g_processImplementations[-1][3] = stripQuotes
    }
    END id:IDENT DOT id2:IDENT SEMI
;


system_implementation 

    :
    SYSTEM IMPL typeid: IDENT DOT defid: IDENT 
    (EXTENDS  unique_impl_name )?
    (refinestypeSubclause)?
    (systemSubcomponents )?
    (cs=connectionsSubclause)?
    (flow_impls)?
    cci=common_component_impl
    END id:IDENT DOT id2:IDENT SEMI
;


data_implementation 

    :
    DATA IMPL typeid: IDENT DOT defid: IDENT 
    (EXTENDS  unique_impl_name )?
    (refinestypeSubclause)?
    (dataSubcomponents )?
    (dataConnectionsSubclause )?            
    cci=common_component_impl
    END id:IDENT DOT id2:IDENT SEMI
;


subprogram_implementation 

    :
    SUBPROGRAM IMPL 
    typeid: IDENT DOT defid: IDENT { 
    if not g_apLevelContainers.has_key(typeid.getText()):
        panic("Line %d: Subprogram (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
    sp = g_apLevelContainers[typeid.getText()]
    g_subProgramImplementations.append([typeid.getText(), defid.getText(), sp._language, "" ]) }
    (EXTENDS  unique_impl_name )?
    (refinestypeSubclause)?
    (callsSubclause)?
    (mesh=connectionsSubclause {
        for conn in mesh:
            if conn._from._portId == None or conn._to._portId == None:
                continue // One of _from,_to are connection_refinements (unsupported)
            sp = g_apLevelContainers[typeid.getText()]
            sp.AddConnection(conn._from, conn._to) } )?
    (flow_impls)?
    c=common_component_impl { 
        if c != None:
            if not g_apLevelContainers.has_key(typeid.getText()):
                panic("Line %d: SUBPROGRAM (%s) must first be declared before it is implemented" % (typeid.getLine(), typeid.getText()))
            sp = g_apLevelContainers[typeid.getText()]
            for assoc in c:
                if assoc == None: continue
                if assoc._name[-15:].lower() == "source_language":
                    stripQuotes = assoc._value.replace("\"", "")
                    //sp.SetLanguage(stripQuotes) 
                    g_subProgramImplementations[-1][2] = stripQuotes
                if assoc._name[-15:].lower() == "fv_name":
                    stripQuotes = assoc._value.replace("\"", "")
                    //sp.SetLanguage(stripQuotes) 
                    g_subProgramImplementations[-1][3] = stripQuotes
    }
    END id:IDENT DOT id2:IDENT SEMI
;


processor_implementation 

    :
    PROCESSOR IMPL typeid: IDENT DOT defid: IDENT 
    (EXTENDS  unique_impl_name )?
    (refinestypeSubclause)?
    (processorSubcomponents)? 
    (busConnectionsSubclause )?             
    (flow_impls)?
    cci=common_component_impl
    END id:IDENT DOT id2:IDENT SEMI
;

memory_implementation 

    :
    MEMORY IMPL typeid: IDENT DOT defid: IDENT 
    (EXTENDS  unique_impl_name )?
    (refinestypeSubclause)?
    (memorySubcomponents )?
    (busConnectionsSubclause )?             
    cci=common_component_impl
    END id:IDENT DOT id2:IDENT SEMI
;

bus_implementation 

    :
    BUS IMPL 
    typeid: IDENT DOT 
    defid: IDENT 
    (EXTENDS  unique_impl_name )?
    (refinestypeSubclause)?
    cci=common_component_impl
    END id:IDENT DOT id2:IDENT SEMI
;

device_implementation 

    :
    DEVICE IMPL 
    typeid: IDENT DOT 
    defid: IDENT 
    (EXTENDS unique_impl_name )?
    (refinestypeSubclause)?
    (flow_impls)?
    cci=common_component_impl
    END id:IDENT DOT id2:IDENT SEMI
;

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ category specific provides clauses
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

featuresData   
    :                
     FEATURES ( ( dataFeature )+ |  none_stmt )
;

dataFeature
    :
    id: IDENT COLON ( REFINED TO  )?  (  data_subprogram | ( PROVIDES  dataAccess ) ) 
;

featuresSubprogram   returns [ subProgramParameters ]
//
    :                
{
    subProgramParameters = []
}
    FEATURES ( ( s=subprogramFeature { subProgramParameters.append(s) } )+ |  none_stmt  )
;

subprogramFeature returns [ subProgramFeature ]
    :
{
   subProgramFeature = None
}
    id: IDENT COLON ( REFINED TO  )?
    (  subprogramPort | port_group_spec 
    |
      ( REQUIRES  dataAccess )
    |  p=parameter { subProgramFeature = AadlSubProgramFeature(id.getText(), p) }
    )
;


featuresThread  returns [threadParameters]
//
    :
{
    threadParameters = []
}
    FEATURES ( ( t=threadFeature { threadParameters.append(t) })+ |  none_stmt  )
;


threadFeature returns [tf]
    :
{
    tf = None
}
    id:IDENT COLON ( REFINED TO  )?
    ( p=port_spec { 
        if p != None:
            tf=AadlThreadFeature(id.getText(), p) 
    } 
    | port_group_spec 
    | server_subprogram 
    | (PROVIDES  dataAccess )
    | (REQUIRES  dataAccess )
    )
;


featuresThreadGroup   
//
    :            
    FEATURES ( ( threadGroupFeature )+ |  none_stmt  )
;


threadGroupFeature
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    ( p=port_spec 
    | port_group_spec 
    | server_subprogram 
    | (PROVIDES dataAccess )
    | (REQUIRES  dataAccess )
    )
;


featuresProcess   returns [fps]
//
    :          
{
    fps = []
}
    FEATURES 
    ( ( p=processFeature { fps.append(p) })+ |  none_stmt )
;


processFeature returns [pf]
    :
{
    pf = None
}
    id: IDENT COLON 
    ( REFINED TO  )?
    (   ps=port_spec { 
        if ps != None:
            pf = AadlProcessFeature(id.getText(), ps) 
    }
    |  port_group_spec 
    |  server_subprogram 
    | (PROVIDES  dataAccess )
    | (REQUIRES  dataAccess )
    )
;


featuresSystem returns [result]
    :
{
    result = []
}
    FEATURES 
    ((  sf=systemFeature { result.append(sf) } )+ |  none_stmt  )
;


systemFeature returns [result]
    :
{
    result = None
}
    id: IDENT COLON 
    ( REFINED TO  )?
    ( p=port_spec { result=p } 
    | port_group_spec 
    | server_subprogram 
    | ( PROVIDES   dataAccess )
    | (PROVIDES  busAccess )
    | (REQUIRES  dataAccess )
    | (REQUIRES  busAccess )
    )
;               


featuresProcessor  
//
    :            
    FEATURES (  (  processorFeature )+ |  none_stmt )
; 


processorFeature
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    ( ps=port_spec 
    | port_group_spec 
    | server_subprogram 
    | (REQUIRES  busAccess )
    )
;               


featuresDevice  
//
    :
    FEATURES ( ( deviceFeature )+ |  none_stmt )
;


deviceFeature
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    ( ps=port_spec 
    | port_group_spec 
    | server_subprogram 
    | ( REQUIRES  busAccess )
    )
;               
        

featuresMemory   
//
    :       
    FEATURES ( ( memoryFeature )+ |  none_stmt  )
;


memoryFeature
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    ( REQUIRES  busAccess )
;


featuresBus   
//
    :
    FEATURES ( ( busFeature )+ |  none_stmt ) 
;


busFeature
    :
    id: IDENT COLON ( REFINED TO  )?  ( REQUIRES  busAccess )
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ refines type subclause
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

refinestypeSubclause 
    : 
    REFINES TYPE 
    ( 
        ( 
        id: IDENT 
        COLON 
        REFINED TO 
            ( p=port_spec 
            | port_group_spec
            | subcomponent_access
            | pa=parameter 
            | server_subprogram
            | data_subprogram
            )
        )+ 
        | 
        ( none_stmt ) 
    )
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 4.5 Subcomponents
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ category specific subcompoennts subclause to reflect acceptable categories
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
threadSubcomponents 
    :                
    SUBCOMPONENTS 
    ( ( threadSubcomponent )+ 
    | ( none_stmt ) )
;


processorSubcomponents
    : 
    SUBCOMPONENTS 
    ( ( processorSubcomponent )+ 
    | ( none_stmt ) )
;


memorySubcomponents
    : 
    SUBCOMPONENTS 
    ( ( memorySubcomponent )+ 
    | ( none_stmt ) )
;


threadgroupSubcomponents
    : 
    SUBCOMPONENTS 
    ( ( threadgroupSubcomponent )+ 
    | ( none_stmt ) )
;


processSubcomponents
    : 
    SUBCOMPONENTS 
    ( ( processSubcomponent )+ 
    | ( none_stmt ) )
;


systemSubcomponents
    : 
    SUBCOMPONENTS 
    ( ( systemSubcomponent )+ 
    | ( none_stmt ) )
;


dataSubcomponents
    : 
    SUBCOMPONENTS 
    ( ( dataSubcomponent )+ 
    | ( none_stmt ) )
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ category specific subcomponent declaration to reflect acceptable categories
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

threadSubcomponent 
    :
    id: IDENT COLON 
    ( REFINED TO )?
    DATA 
    subcomponent_decl 
;


threadgroupSubcomponent 
    :
    id: IDENT COLON 
    ( REFINED TO )?
    ( DATA | THREAD GROUP | THREAD )
    subcomponent_decl 
;


dataSubcomponent 
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    DATA 
    subcomponent_decl 
;


processSubcomponent 
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    ( DATA | THREAD GROUP | THREAD )
    subcomponent_decl 
;


processorSubcomponent 
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    MEMORY 
    subcomponent_decl 
;


memorySubcomponent 
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    MEMORY 
    subcomponent_decl 
;


systemSubcomponent 
    :
    id: IDENT COLON 
    ( REFINED TO  )?
    ( DATA | MEMORY | PROCESSOR | BUS | DEVICE | PROCESS | SYSTEM ) 
    subcomponent_decl 
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ common part of subcomponent declaration
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

subcomponent_decl 
    :
    ( cr=classifier_reference )?
    (containedCurlyPropertyAssociations )?
    (in_modes)? SEMI 
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 4.6 Annex Subclasses
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// **** set up gammar to let everything but **} through

annex_library 

    :
    ANNEX id:IDENT at : ANNEX_TEXT SEMI
;


annex_subclause 

    : 
    ANNEX id:IDENT at : ANNEX_TEXT SEMI 
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 5 PROPERTIES
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 5.1 Property Sets
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// We must support multiple property type, name, and constant definitions in one declaration
// This is done through the list of defining identifiers
// A pain in the neck to process. We must first construct the whole thing, then dupliate it.
// The addition of the items into the propertyset is subclass specific, thus, ps and the list of identifeir strings are passed in as paramters

// Standalone property set in a separate file
propertyset_file 

    :
    PROPERTY SET ps_id:IDENT IS
    (   
        id: IDENT COLON
        (
            property_constant 
            | property_type_declaration 
            | property_name_declaration
        )
    )+
    END ps_id2:IDENT SEMI
    EOF
;


// Nested property set inside an Aadl specification
property_set 

    :
    PROPERTY SET ps_id: IDENT IS
    (   
        id: IDENT COLON
        (
            property_constant 
            | property_type_declaration 
            | property_name_declaration
        )
    )+
    END ps_id2:IDENT SEMI
;

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 5.1.1 Property Types
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// Property type can be named, i.e., defined with a list of identifiers.
// this means they must be replicated.
// They can also be declared as unnamed types as part of property name declarations.
// In that case they are a single instance with no name. Thus, two rules for every property type.

// ParsedPropertyReference object is used to hold the parsed idendieirs. 
// This is used for references to other properties, from property associaitons to property names,
// references to units literals, and enumeration literals. The objects are processed by the name resolver.

property_type_declaration  

    :
    TYPE property_type SEMI
;

property_type 
    :
    boolean_type
    | string_type
    | enumeration_type | units_type
    | real_type | integer_type 
    | range_type
    | classifier_type
    | component_property_type
;


unnamed_property_type 
    :
    unnamed_boolean_type
    | unnamed_string_type
    | unnamed_enumeration_type | unnamed_units_type
    | unnamed_real_type | unnamed_integer_type 
    | unnamed_range_type
    | unnamed_classifier_type
    | unnamed_component_property_type
;


unnamed_boolean_type  
    :
    BOOLEAN  
;


boolean_type 
    :
    BOOLEAN 
;


string_type  
    :
    STRING 
;
 

unnamed_string_type  
    :
    STRING  
;
 

enumeration_type 
    :
    unnamed_enumeration_type
;


unnamed_enumeration_type 
    :
    ENUMERATION
    LPAREN lit: IDENT  
    ( COMMA morelit:IDENT )* RPAREN 
;
          

units_type 
    :
    UNITS units_list
;


unnamed_units_type 
    :
    UNITS units_list
;


units_list 
    :
    LPAREN lit:IDENT
    ( COMMA morelit: IDENT ASSIGN unitid: IDENT STAR number_value )* RPAREN
;


real_type 
    :
    unnamed_real_type
;    


unnamed_real_type 
    :
    REAL 
    ( real_range )?   
    ( UNITS ( unique_property_type_identifier | units_list ) )?
;    


integer_type 
    :
    unnamed_integer_type
;    


unnamed_integer_type 
    :
    i:INTEGER 
    (integer_range )? 
    ( UNITS (unique_property_type_identifier | units_list ))?
;


// For these next rules we know that we have only reals or only integers due to a preceding reserverd word
// We also know that any identiifier is a reference to a property constant of the appropriate type.
// Those references are recorded as ParsedPropertyReferences with the RealValue and IntegerValue instead of the generic reference class

real_range 
    :
    signed_aadlreal_or_constant DOTDOT signed_aadlreal_or_constant 
;


integer_range 
    :
    signed_aadlinteger_or_constant DOTDOT signed_aadlinteger_or_constant 
;


// real literal with an optional sign and unit
signed_aadlreal 
    :
    ( PLUS | MINUS )?  
    ( real_literal )
    // optional unit
    ( ui:IDENT )?
;


// real literal with optional sign, named reference with or without sign
// Note that here we know that an identifier is referring to a real
signed_aadlreal_or_constant 
    :
    signed_aadlreal
    |
    ( ( PLUS | MINUS )?  property_name_constant_reference )
;


// integer literal with optional sign and unit
signed_aadlinteger 
    :
    ( PLUS | MINUS )?  
    ( integer_literal )
    // optional unit
    ( ui:IDENT )?
;


// integer literal with optional sign and unit, named reference with or without sign
// Note that here we know that an identifier is referring to a integer
signed_aadlinteger_or_constant 
    :
    signed_aadlinteger
    | 
    ( ( PLUS | MINUS  )?  property_name_constant_reference )
;       


// numeric literal with optional sign and unit
signed_aadlnumeric returns [retValue]
    :
{
    retValue = None
}
    ( PLUS | MINUS )?  
    ( numericval: NUMERIC_LIT { retValue = numericval.getText() } )
    // optional unit
    ( ui:IDENT )?
;


// numeric literal without optional sign and unit
number_value 
    :
    ( numericval: NUMERIC_LIT )
;


// real literal with optional sign, named reference with or without sign
// Note that here we know that an identifier is referring to a real
signed_aadlnumeric_or_constant 
    :
    s=signed_aadlnumeric | ( ( PLUS | MINUS  )?  property_name_constant_reference )
;


// real literal with optional sign, named reference with or without sign
// Note that here we know that an identifier is referring to a real
signed_aadlnumeric_or_signed_constant returns [retValue]
    : 
{
    retValue = None
}
    s=signed_aadlnumeric { retValue = s } | ( ( PLUS | MINUS ) property_name_constant_reference )
;


// note that in case of the range type any name references in the range are created in terms of Real or Integer objects with a ParsedProeprtyReference    
unnamed_range_type 
    :
    RANGE OF ( unnamed_real_type | unnamed_integer_type | unique_property_type_identifier )
;


range_type 
    :
    unnamed_range_type
;


unnamed_classifier_type 
    :
    CLASSIFIER ( LPAREN  component_category ( id: COMMA component_category )* RPAREN )?
;

        
classifier_type 
    :
    unnamed_classifier_type
;


unnamed_component_property_type 
    :
    REFERENCE ( LPAREN referable_element_category ( id:COMMA referable_element_category )* RPAREN )?
;
    
        
component_property_type 
    :
    unnamed_component_property_type
;


referable_element_category :
    ( THREAD GROUP 
    | THREAD 
    | DATA 
    | SUBPROGRAM 
    | PROCESS 
    | PROCESSOR 
    | MEMORY 
    | BUS 
    | DEVICE 
    | SYSTEM  
    | CONNECTIONS 
    | SERVER SUBPROGRAM 
    )
;


unique_property_type_identifier 
    :
    ( pset: IDENT DOUBLECOLON )? ptype: IDENT 
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 5.1.2 Property Names
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
property_name_declaration 

    :
    ( ACCESS  )?
    ( INHERIT  )?
    ( single_valued_property | multi_valued_property )
    APPLIES TO
    LPAREN 
    ( (  property_owner ( COMMA property_owner )* ) 
           | ( ALL 
           // set all values by hand
    ) )
    RPAREN SEMI
;

property_owner 
    :
    ( id1:THREAD GROUP 
    | id2:THREAD 
    | id3:DATA 
    | id4:SUBPROGRAM 
    | id5:PROCESS 
    | id6:PROCESSOR 
    | id7:MEMORY 
    | id8:BUS 
    | id9:DEVICE 
    | id10:SYSTEM  
    | id11:CONNECTIONS 
    | id12:SERVER SUBPROGRAM 
    | id13:MODE 
    | id14:PORT GROUP CONNECTIONS 
    | id15:PORT GROUP 
    | id16:PORT CONNECTIONS 
    | id17:PORT 
    | id18:DATA PORT 
    | id19:EVENT DATA PORT 
    | id20:EVENT PORT 
    | id21:DATA PORT CONNECTIONS 
    | id22:EVENT DATA PORT CONNECTIONS 
    | id23:EVENT PORT CONNECTIONS 
    | id24:FLOW 
    | id25:ACCESS CONNECTIONS 
    | id26:PARAMETER 
    | id27:PARAMETER CONNECTIONS )
    ( cr=classifier_reference  )?
;

single_valued_property 
    :
    ( 
        unnamed_property_type 
    | 
        unique_property_type_identifier
    )
    ( ASSIGN pe=property_expression )?
;


multi_valued_property 
    :
    LIST OF ( unnamed_property_type | unique_property_type_identifier )
    ( ASSIGN LPAREN ( pe=property_expression ( COMMA pe=property_expression )* )?  RPAREN )?
;



// Note that for property constants we know we are dealing with reals and integers,
// even when identifiers are used - they refer to other constants
// As a result we create the respective Value objects and attach the ParsedPropertyReference object to it.


property_constant 

    :
    CONSTANT  (single_valued_property_constant | multi_valued_property_constant) SEMI
;
     
single_valued_property_constant 
    :
    (
     ( INTEGER ( unique_property_type_identifier )?  ASSIGN signed_aadlinteger )
     | ( REAL ( unique_property_type_identifier )?  ASSIGN signed_aadlreal )
     | ( STRING ASSIGN st=string_term )
     | ( BOOLEAN ASSIGN true_false_value )
     | ( unique_property_type_identifier ASSIGN 
         (
          et=enumeration_term 
          | 
          ( ( (s=signed_aadlnumeric DOTDOT) => aadl_numeric_range | ss=signed_aadlnumeric ) )
         )
       )
    ) 
;


     
multi_valued_property_constant 
    :
    LIST OF 
    (
        ( INTEGER ( unique_property_type_identifier  )?  
          ASSIGN LPAREN ( signed_aadlinteger ( COMMA signed_aadlinteger )* )?  RPAREN )
    |
        ( REAL ( unique_property_type_identifier  )?
          ASSIGN LPAREN ( signed_aadlreal ( COMMA signed_aadlreal )*)?  RPAREN )
    |
        ( STRING 
          ASSIGN LPAREN (st=string_term ( COMMA ste=string_term )*)?  RPAREN )
    |   
        ( BOOLEAN 
          ASSIGN LPAREN ( true_false_value ( COMMA true_false_value )*)?  RPAREN )
    |   
        ( 
            unique_property_type_identifier ASSIGN LPAREN
            ( 
                ( et=enumeration_term ( COMMA ete=enumeration_term )* )
            |
                ( 
                    (signed_aadlnumeric DOTDOT) => ( aadl_numeric_range ( COMMA aadl_numeric_range )* )
                     |
                    ( s=signed_aadlnumeric ( COMMA ss=signed_aadlnumeric )* )
                )  // signed_aadlnumeric DOTDOT
            )?
            RPAREN
        )
    )
;


aadl_numeric_range 
    :
    s=signed_aadlnumeric
    DOTDOT ss=signed_aadlnumeric
    ( DELTA sss=signed_aadlnumeric)?
;

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 5.3 Property Associations
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

propertyAssociations 
//
    :
    PROPERTIES 
    (none_stmt | (  p=property_association )+ ) 
;


containedPropertyAssociations returns [ listOfProperties ]
//
    :
{
    listOfProperties = []
}
    PROPERTIES (none_stmt | (  c=contained_property_association { listOfProperties.append(c) })+ ) 
;


propertyAssociations_no_modes returns [tupleOfProperties]
//
    :
{
    tupleOfProperties = []
}
    PROPERTIES (none_stmt | (  panm=property_association_no_modes { tupleOfProperties.append(panm) } )+ ) 
;


curlyPropertyAssociations 

    :
    LCURLY ( pa=property_association )+ RCURLY  
;


curlyPropertyAssociations_no_modes returns [ tupleOfProperties ]

    :
{
    tupleOfProperties = []
}
    LCURLY ( panm=property_association_no_modes { tupleOfProperties.append(panm) } )+ RCURLY  
;


containedCurlyPropertyAssociations 
    :
    LCURLY ( cpa=contained_property_association )+ RCURLY  
;


property_association returns [retValue]
//
    :
{
    retValue = None
}
    pnr=property_name_reference 
    ( ASSIGN | ASSIGNPLUS )
    ( CONSTANT )?
    ( ACCESS )?
    p=pe_or_list { retValue = p }
    ( in_binding )?
    ( in_modes )?
    SEMI
;

property_association_no_modes returns [retValue]
//
    :
{
    retValue = None
}
    pnr=property_name_reference 
    ( ASSIGN | ASSIGNPLUS  )
    ( CONSTANT  )?
    ( ACCESS  )?
    p=pe_or_list { retValue = AadlPropertyAssociationNoModes(pnr, p) }
    ( in_binding )?
    SEMI
;

property_name_reference returns [retValue]
    :
    { retValue = None }
    ( psid:IDENT DOUBLECOLON )?  pid:IDENT  { retValue = pid.getText() }
;


property_name_constant_reference 
    :
    VALUE LPAREN pnr=property_name_reference RPAREN
;

// NOTE: This is not exactly the same as the contained_property_assocation rule in the
// spec.  In this case, "contained_property_assocation" is used whereever contained
// property assocations are allowed, and thus this rule really handles both normal and
// contained property associations.
contained_property_association returns [retValue]
    :
{
    retValue = None
}
    p1=property_name_reference
    ( ASSIGN | ASSIGNPLUS  )
    ( CONSTANT )?
    p2=pe_or_list { retValue = AadlContainedPropertyAssociation(p1, p2) }
    ( applies_to )?
    ( in_binding )?
    ( in_modes )?
    SEMI
;

applies_to 
    :
    APPLIES TO cid: IDENT ( DOT mid: IDENT )* 
;


in_binding  
    :
    IN BINDING LPAREN cr=classifier_reference ( COMMA cr=classifier_reference )* RPAREN
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 5.4 Property Expressions
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


pe_or_list returns [retValue]
    :
    {
        retValue = None
    }
    ( 
        LPAREN pe1=property_expression COMMA ) => 
        (LPAREN pe2=property_expression ( COMMA pe3=property_expression )+ RPAREN)
    |
        (LPAREN ( a=allbutbool {if a != None: retValue = a} )?  RPAREN)
    | 
        ( a=allbutbool { if a != None: retValue = a })
    |
        (
            ( property_name_constant_reference DOTDOT ) =>
            ( property_name_constant_reference num_range )
        |       
            ( logical_or )
        )
;


allbutbool returns [retValue]
    :
{
    retValue = None 
}
    reference_term 
    | e=enumeration_term { retValue = e }
    | s=string_term { retValue = s }
    | c=component_classifier_term { retValue = c }
    | n=numeric_or_range_term { retValue = n }
;


property_expression returns [retValue]
    :
{
    retValue = None
}
//   property_term is already covered in boolean expression (logical_or)
    n=numeric_or_range_term 
    | reference_term 
    | e=enumeration_term
    | s=string_term  { retValue = s }
    | c=component_classifier_term { retValue = c }
    | logical_or 
;


logical_or 
    :
    logical_and ( OR logical_and )*
;

    
logical_and 
    :
    logical_unary ( AND logical_unary )*
;

    
logical_unary 
    :
    tv:TRUE 
    | fv:FALSE 
    | LPAREN logical_or RPAREN 
    | nott:NOT logical_unary 
    | property_term
;


true_false_value 
    :
    tv:TRUE 
    | fv:FALSE 
;


signed_constant 
    :
    ( PLUS | MINUS  ) property_name_constant_reference 
;


// this rule handles integers, reals, as well as ranges of both types
// This includes the use of identifiers when they are preceded by a sign
// or all identifiers in the max and delta part of ranges
// Those references are represented as IntegerValue if known, with a ParsedPropertyReference object.
// Otherwise they are represented as RealValue - it may have to be recast into an IntergerValue at the time of name resolution.

numeric_or_range_term returns [retValue]
    :
{
    retValue = None
}
        ( signed_constant DOTDOT ) => ( signed_constant num_range )
    |
        ( s=signed_aadlnumeric_or_signed_constant { retValue = s } ( num_range )? )
;


// support rule to handle remainder of range if DOTDOT is identified in look ahead
num_range  
    :
    DOTDOT signed_aadlnumeric_or_constant ( DELTA signed_aadlnumeric_or_constant )?
;


string_term returns [retValue]
    :
    sl: STRING_LITERAL { retValue = sl.getText() }
;


enumeration_term returns [retValue]
    :
    enum_id: IDENT  { retValue = enum_id.getText() }
;


property_term 
    :
    property_name_constant_reference
;


component_classifier_term returns [result]
    :
{
    result = None
}
    c=component_category ( cr=classifier_reference { result = cr })?
;


component_category 
    :
    ( THREAD GROUP )
    | THREAD 
    | DATA 
    | SUBPROGRAM 
    | PROCESS 
    | PROCESSOR 
    | MEMORY 
    | BUS 
    | DEVICE 
    | SYSTEM  
;


// ** may be the same as the instance association
reference_term 
    :
    REFERENCE subcomponentid: IDENT 
    ( DOT subcomponentidmore: IDENT )*
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 6.2 Subprograms
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

callsSubclause 
    :
    CALLS  ( ( subprogram_call_sequence )+ |  none_stmt  )
;


subprogram_call_sequence 
    :
    ( id: IDENT COLON )?
    LCURLY ( subprogram_call )+ RCURLY
    ( in_modes )? 
    SEMI
;


subprogram_call 
    :
    defcallid:IDENT COLON SUBPROGRAM called_subprogram  
    ( curlyPropertyAssociations  )? 
    SEMI 
;


called_subprogram 
    :
//      data_identifier DOT data_subprogram_identifier | unique_subprogram_classifier_reference
    cr=classifier_reference  
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 8.2 Modes
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

mode_subclause 
    :               
    MODES  ( (mode)* ( mode_transition )*  | none_stmt )
;

mode 
    :
    id:IDENT COLON 
    ( INITIAL  )?
    ( REFINED TO )?
    MODE  
    ( curlyPropertyAssociations  )?
    SEMI 
;


mode_transition 
    :
    id: IDENT 
    ( COMMA moreid: IDENT )*
    LTRANS up1=unique_port_identifier 
    ( COMMA up2=unique_port_identifier )* 
    RTRANS
    destination_mode:IDENT 
    SEMI 
;


unique_port_identifier returns [retValue]
    :
    compid:IDENT DOT portid:IDENT { retValue = UniquePortIdentifier(compid.getText(), portid.getText()) }
    |
    soleportid:IDENT { retValue = UniquePortIdentifier(None, soleportid.getText()) }
;
  
 
// phf *** details for rule above: unique_port_identifier :
//    component_type_port_identifier
//      | subcomponent_identifier "." port_identifier
//  | component_type_port_group_identifier "." port_identifier


in_modes 
    :
    IN MODES
    LPAREN 
    ( 
        ( m1:IDENT 
            
                
                ( COMMA m2:IDENT 
                )* 
        ) 
        | NONE 
    ) RPAREN;
    

in_modes_and_transitions 
    :
    IN MODES
    LPAREN ( 
        ( mode_or_transition 
                ( COMMA mode_or_transition )* 
        ) 
        | NONE 
    ) RPAREN // extra parens
;


mode_or_transition 
    :
    mode_id: IDENT 
    |
    LPAREN old_mode_id:IDENT ARROW new_mode_id:IDENT RPAREN
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 9 FEATURES AND SHARED ACCESS
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// specific features are called in category specific provides clauses
//feature :
//    port_spec | server_subprogram | subprogram_spec |
//    subcomponent_access ;
// phf: the subrules are used selectively

//feature_refinement returns :
//    ft = port_refinement |
//    ft = server_subprogram_refinement | ft = data_subprogram_refinement |
//    ft = subcomponent_access_refinement 
//    ;
// phf: refines is handled as part of the regular rule
                        
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 9.1 Ports
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
port_spec returns [ portSpecification ]
    :
{
    portSpecification = None
    direction = None
}
    ( 
        IN OUT { direction = "INOUT" }
    | 
        IN { direction = "IN" }
    | 
        OUT { direction = "OUT" }
    ) 
    p=port_type  { 
        if p != None:
            portSpecification = p
            p._direction = direction
            portSpecification._encoding = "UPER"
    }
    ( cpa=curlyPropertyAssociations_no_modes {
        if portSpecification != None:
            encodings = [x._propertyExpressionOrList for x in cpa if x._name.lower()[-8:] == "encoding"]
            if 1 == len(encodings):
                portSpecification._encoding = encodings[0].capitalize()
            calledSubprograms = [x._propertyExpressionOrList for x in cpa if x._name.lower()=="rcmoperation"]
            if 1 == len(calledSubprograms):
                assert( isinstance(portSpecification, AadlEventPort) )
                portSpecification._sp = calledSubprograms[0][2:]
    } )?
    SEMI 
;

         
port_type returns [ port ]
    :
{
    portType = None
}
    (EVENT DATA PORT ( c=classifier_reference { port = AadlEventDataPort("", c) } )? ) 
    |
    (DATA PORT ( c=classifier_reference { port = AadlPort("", c) } )? ) 
    | 
    (EVENT PORT { port = AadlEventPort("", None) } ) 
;
    

subprogramPort 
    :
    (  OUT  EVENT PORT |  OUT EVENT DATA PORT ( cr=classifier_reference )? )
    ( cpa=curlyPropertyAssociations_no_modes   )?  SEMI
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 9.2 Subprograms
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
data_subprogram 
    :
    SUBPROGRAM
    ( cr=classifier_reference  )?
    ( cpa=curlyPropertyAssociations_no_modes )?
    SEMI
;


server_subprogram 
    :
    SERVER 
    SUBPROGRAM
    ( unique_subprogram_reference  )?
    ( cpa=curlyPropertyAssociations_no_modes )?
    SEMI
;


unique_subprogram_reference 
    :
    ( pid: IDENT DOUBLECOLON )* tid:IDENT ( DOT iid:IDENT )?
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 9.3 Component Parameters
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

parameter returns [ param ]
    :
{
    direction = None
    param = None
}
    ( 
        IN OUT { direction = "INOUT" }
    | 
        IN { direction = "IN" }
    | 
        OUT { direction = "OUT" }
    ) 
    PARAMETER
    ( c=classifier_reference { 
        param = AadlParameter(direction, c) 
        param._encoding = "UPER"
    } )?
    ( cpa=curlyPropertyAssociations_no_modes { 
        if param != None:
            encodings = [x._propertyExpressionOrList for x in cpa if x._name.lower()[-8:] == "encoding"]
            if 1 == len(encodings):
                param._encoding = encodings[0].capitalize()
      } )?
    SEMI
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 9.4 Subcomponent Acess
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
dataAccess  
    :
    DATA ACCESS 
    ( c=classifier_reference )?
    ( cpa=curlyPropertyAssociations_no_modes )?
    SEMI
;


busAccess  
    :
    BUS ACCESS 
    ( cr=classifier_reference  )?
    ( cpa=curlyPropertyAssociations_no_modes  )?
    SEMI
;


subcomponent_access 
    :
    REQUIRES dataAccess 
    | REQUIRES busAccess 
    | PROVIDES dataAccess 
    | PROVIDES busAccess 
    ;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 9.5 Port Groups
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
port_group_type 
    :
    PORT GROUP defid:IDENT 
    ( EXTENDS unique_type_name )?
    (
        ( 
            FEATURES
            ( id: IDENT COLON ( REFINED TO  )?  (p=port_spec | port_group_spec) )*
            ( INVERSE OF unique_type_name )?
        )
        |
        ( INVERSE OF unique_type_name )
    )
    ( pa=propertyAssociations_no_modes  )?
    ( annex_subclause  )?
    END id2:IDENT SEMI
;


port_group_spec 
    :
    PORT GROUP
    ( unique_type_name  )?
    ( cpa=curlyPropertyAssociations_no_modes  )?
    SEMI
;


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//@@ Section 10 CONNECTIONS
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
connectionsSubclause returns [retValue]
    :
{
    retValue = []
}
     CONNECTIONS  (( c=connection { if c!=None: retValue.append(c) } | cf=connection_refinement )+ | ( none_stmt ))
;


connection returns [retValue] 
    :
{
    retValue = None
}
    ( id:IDENT COLON  )?
    (  d=data_connection { retValue = d }
     | e=event_data_connection { retValue = e }
     | ev=event_connection { retValue = ev }
     | p=port_group_connection { retValue = p }
     | pc=parameter_connection { retValue = pc }
     | b=bus_access_connection { retValue = b }
     | da=data_access_connection { retValue = da }
    )
    ( curlyPropertyAssociations  )?
    ( in_modes_and_transitions )? SEMI
;

data_connection returns [retValue]
    :
    DATA PORT u1=unique_port_identifier ( ARROW | DARROW ) u2=unique_port_identifier 
{
    retValue = Connection(u1, u2)
}
;

//-------------------------------------------------------------------

event_connection returns [retValue]
    :
    EVENT PORT u1=unique_port_identifier ARROW u2=unique_port_identifier
{
    retValue = Connection(u1, u2)
}
;

//-------------------------------------------------------------------
event_data_connection returns [retValue]
    :
    EVENT DATA PORT u1=unique_port_identifier ARROW u2=unique_port_identifier
{
    retValue = Connection(u1, u2)
}
;

//-------------------------------------------------------------------
parameter_connection returns [retValue]
    :
    PARAMETER u1=unique_port_identifier ARROW u2=unique_port_identifier
{
    retValue = Connection(u1, u2)
}
;

//-------------------------------------------------------------------
bus_access_connection returns [retValue]
    :
    BUS ACCESS u1=unique_port_identifier ARROW u2=unique_port_identifier
{
    retValue = Connection(u1, u2)
}
;

//-------------------------------------------------------------------
data_access_connection  returns [retValue]
    :
    DATA ACCESS u1=unique_port_identifier ARROW u2=unique_port_identifier
{
    retValue = Connection(u1, u2)
}
;

//-------------------------------------------------------------------
port_group_connection  returns [retValue]
    :
    PORT GROUP u1=unique_port_group_identifier ARROW u2=unique_port_group_identifier
{
    retValue = Connection(u1, u2)
}
;

unique_port_group_identifier returns [retValue]
    :
    compid:IDENT DOT portid:IDENT { retValue = UniquePortIdentifier(compid.getText(), portid.getText()) } 
|
    soleportid:IDENT { retValue = UniquePortIdentifier(None, portid.getText()) } 
//       subcomponent_identifier:IDENT DOT port_group_identifier:IDENT
//       |
//       component_type_port_group_identifier:IDENT DOT element_port_group_identifier:IDENT
//       |
//       component_type_port_group_identifier:IDENT  // reordered because of no dot
;

connection_refinement returns [retValue]
    :
{
    retValue = UniquePortIdentifier(None, None) // Don't handle these yet
}
     id:IDENT COLON REFINED TO
     ( EVENT DATA PORT 
     | EVENT PORT 
     | DATA PORT 
     | PORT GROUP 
     | PARAMETER 
     | BUS ACCESS 
     | DATA ACCESS 
     )
     (
        ( curlyPropertyAssociations ( in_modes_and_transitions )? ) 
        |
        in_modes_and_transitions
     )
     SEMI
;


dataConnectionsSubclause 
    :               
    CONNECTIONS  
    (
        ( 
            data_access_connection_decl 
            | 
            data_access_connection_refinement_decl 
        )+ 
        | 
        ( none_stmt )
    )
;


data_access_connection_decl 
    :
    ( id:IDENT COLON  )?
    dac=data_access_connection 
    ( curlyPropertyAssociations  )?
    ( in_modes )? SEMI
;

data_access_connection_refinement_decl 
    :
    id:IDENT COLON REFINED TO
    DATA ACCESS 
    (
        ( curlyPropertyAssociations ( in_modes )? ) 
        |
        in_modes
    )
    SEMI
;


busConnectionsSubclause 
    :               
    CONNECTIONS  
    (
        ( bus_access_connection_decl | bus_access_connection_refinement_decl )+ 
        | 
        ( none_stmt )
    )
;


bus_access_connection_decl 
    :
    ( id:IDENT COLON  )?
    bac=bus_access_connection 
    ( curlyPropertyAssociations  )?
    ( in_modes )? SEMI
;

bus_access_connection_refinement_decl 
    :
    id:IDENT COLON REFINED TO BUS ACCESS 
    (
        ( curlyPropertyAssociations ( in_modes )?) 
        |
        in_modes
    )
    SEMI
;


//-------------------------------------------------------------------
//@
//@   End-To-End Flows
//@

flow_specs
    : 
    FLOWS 
    ( (flow_spec)+ | none_stmt )
;


flow_spec 
    :
    defining_identifier:IDENT COLON 
    ( 
        flow_source_spec
        | flow_sink_spec
        | flow_path_spec 
        | ( REFINED TO ( flow_source_spec_refinement | flow_sink_spec_refinement | flow_path_spec_refinement ) )
     )
     SEMI
;

flow_source_spec 
    : 
    FLOW SOURCE 
    flow_feature_identifier
    ( cpa=curlyPropertyAssociations_no_modes )?
;


flow_source_spec_refinement 
    : 
    FLOW SOURCE 
    cpa=curlyPropertyAssociations_no_modes 
;


flow_sink_spec 
    : 
    FLOW SINK 
    flow_feature_identifier
    ( cpa=curlyPropertyAssociations_no_modes )?
;


flow_sink_spec_refinement 
    : 
    FLOW SINK 
    cpa=curlyPropertyAssociations_no_modes 
;


flow_path_spec 
    : 
    FLOW PATH
    flow_feature_identifier ARROW 
    flow_feature_identifier
    ( cpa=curlyPropertyAssociations_no_modes )?
;


flow_path_spec_refinement 
    : 
    FLOW PATH cpa=curlyPropertyAssociations_no_modes 
;


flow_impls
    : 
    FLOWS ( ( flow_sequence  )+ | none_stmt )
;


flow_sequence  
    :
    defining_identifier:IDENT 
    COLON 
    ( flow_source_implementation
    | flow_sink_implementation
    | flow_path_implementation 
    | end_to_end_flow 
    | ( REFINED TO 
         ( flow_source_implementation_refinement
         | flow_sink_implementation_refinement
         | flow_path_implementation_refinement 
         | end_to_end_flow_refinement 
         )
        )
    )
    SEMI
;

flow_source_implementation 
    :
    FLOW SOURCE
    ( subcomponent_flow_identifier ARROW connection_identifier ARROW )*
    flow_feature_identifier 
    ( curlyPropertyAssociations )?
    ( in_modes )?
;


flow_sink_implementation 
    :
    FLOW SINK 
    flow_feature_identifier 
    ( ARROW connection_identifier ARROW subcomponent_flow_identifier )*
    ( curlyPropertyAssociations )?  
    ( in_modes )?
;


flow_path_implementation 
    :
    FLOW PATH 
    flow_feature_identifier 
    ARROW 
    ( connection_identifier ARROW (subcomponent_flow_identifier ARROW  connection_identifier ARROW )+ )?
    flow_feature_identifier 
    ( curlyPropertyAssociations )?
    ( in_modes )?
;


flow_source_implementation_refinement 
    :
    FLOW SOURCE
    ( 
        curlyPropertyAssociations ( in_modes )?
    |  
        in_modes 
    )?
;


flow_sink_implementation_refinement 
    :
    FLOW SINK 
    ( 
        curlyPropertyAssociations ( in_modes )?
        |  
        in_modes 
    )?
;


flow_path_implementation_refinement 
    :
    FLOW PATH
    ( 
        curlyPropertyAssociations ( in_modes )?
        |  
        in_modes 
    )?
;


subcomponent_flow_identifier  
    :
    subcompid:IDENT DOT flowid:IDENT 
;


end_to_end_flow 
    :
    END TO END FLOW  
    subcomponent_flow_identifier 
    ( ARROW connection_identifier ARROW subcomponent_flow_identifier )+
    ( curlyPropertyAssociations )? 
    ( in_modes )?
;


end_to_end_flow_refinement 
    :
    END TO END FLOW 
    ( 
        curlyPropertyAssociations ( in_modes )?
        |  
        in_modes 
    )?
;


connection_identifier 
    :
    connid:IDENT 
;


flow_feature_identifier 
    :
    compid:IDENT DOT portid:IDENT 
    |
    soleportid:IDENT 
//     port_identifier
//     | parameter_identifier
//     | port_group_identifier
//     | port_group_identifier DOT port_identifier
;


real_literal 
    :
    id:NUMERIC_LIT
;

        
integer_literal 
    :
    id:NUMERIC_LIT
;


class AadlLexer extends Lexer;

options {
    k=3; // needed for newline junk
    charVocabulary='\u0000'..'\uFFFE'; // allow UNICODE
    caseSensitive = false;
    caseSensitiveLiterals = false;
    defaultErrorHandler=true;
}

tokens {
    AADLSPEC;
    ACCESS="access";
    AND="and";
    ALL="all";
    ANNEX="annex";
    APPLIES="applies";
    BINDING="binding";
    BOOLEAN="aadlboolean";
    BUS="bus";
    CALLS="calls";
    CLASSIFIER="classifier";
    REFERENCE="reference";
    CONNECTIONS="connections";
    CONSTANT="constant";
    DATA="data";
    DELTA="delta";
    DEVICE="device";
    END="end";
    ENUMERATION="enumeration";
    EVENT="event";
    EXTENDS="extends";
    FALSE="false";
    FEATURES="features";
    FLOW="flow";
    FLOWS="flows";
    GROUP="group";
    IMPL="implementation";
    IN="in";
    INHERIT="inherit";
    INITIAL="initial";
    INTEGER="aadlinteger";
    INVERSE="inverse";
    IS="is";
    LIST="list";
    MEMORY="memory";
    MODE="mode";
    MODES="modes";
    NONE = "none";
    NOTT="not";
    OF="of";
    OR="or";
    OUT="out";
    PACKAGE="package";
    PARAMETER="parameter";
    PATH="path";
    PORT="port";
    PRIVATE="private";
    PROCESS="process";
    PROCESSOR="processor";
    PROPERTIES="properties";
    PROPERTY="property";
    PROVIDES="provides";
    PUBLIC="public";
    RANGE="range";
    REAL="aadlreal";
    REFINED="refined";
    REFINES="refines";
    REQUIRES = "requires";
    SERVER="server";
    SET = "set";
    SINK="sink";
    SOURCE="source";
    STRING="aadlstring";
    SUBCOMPONENTS="subcomponents";
    SUBPROGRAM="subprogram";
    SYSTEM="system";
    THREAD="thread";
    TO="to";
    TRANSITIONS="transitions";
    TRUE="true";
    TYPE="type";
    UNITS="units";
    VALUE="value";
}
 
LPAREN      : '(' ;
RPAREN      : ')' ;
LCURLY      : '{' ;
RCURLY      : '}' ;
COLON       :  ':' ;
PLUS        : '+' ;
MINUS       : '-' ;
STAR        : '*' ;
SEMI        : ';' ;
COMMA       : ',' ;
DOT         : '.' ;
DOTDOT      : ".." ;
ASSIGN      : "=>";
ASSIGNPLUS  : "+=>";
DOUBLECOLON : "::";
LTRANS      : "-[";
RTRANS      : "]->";
ARROW       : "->" ;
DARROW      : "->>";
HASH        : '#';
  
IDENT
    :  ('a'..'z'
        //|'A'..'Z'
        ) ( ('_')? ('a'..'z'
        //|'A'..'Z'
        |'0'..'9'))*
    exception
        catch [antlr.RecognitionException ex] {
            self.reportError(ex);
            self.consume();
        }
;


// string literals
STRING_LITERAL
    :
    '"' (ESC|~('"'|'\\'))* '"'
;


NUMERIC_LIT 
    : 
    ( DIGIT )+
    (( '#' BASED_INTEGER  '#' ( INT_EXPONENT )? )
    | ( '_' ( DIGIT )+ )*  // INTEGER
      ( { LA(2)!='.' }?  //&& LA(3)!='.' }?
                    // real
            ( '.' ( DIGIT )+ ( '_' ( DIGIT )+ )* ( EXPONENT )?)
                    // integer with exponent
            | (INT_EXPONENT)?
      )
    )
    exception
        catch [antlr.RecognitionException ex] {
            self.reportError(ex);
            self.consume();
        }
;



// a couple protected methods to assist in matching the various numbers

protected
DIGIT   :  ( '0'..'9' ) ;

protected
EXPONENT           :  ('e') ('+'|'-')? ( DIGIT )+ ;

protected
INT_EXPONENT           :  ('e') ('+')? ( DIGIT )+ 
                        exception
          catch [antlr.RecognitionException ex] {
            self.reportError(ex);
            self.consume();
          }
;


protected
EXTENDED_DIGIT     :  ( DIGIT | 'a'..'f' ) ;

protected
BASED_INTEGER      :  ( EXTENDED_DIGIT ) ( ('_')? EXTENDED_DIGIT )* ;

protected
BASE                            : DIGIT ( DIGIT )?
;

// escape sequence -- note that this is protected; it can only be called
//   from another lexer rule -- it will not ever directly return a token to
//   the parser
// There are various ambiguities hushed in this rule.  The optional
// '0'...'9' digit matches should be matched here rather than letting
// them go back to STRING_LITERAL to be matched.  ANTLR does the
// right thing by matching immediately; hence, it's ok to shut off
// the FOLLOW ambig warnings.
protected
ESC
        :       '\\'
                (       'n'
                |       'r'
                |       't'
                |       'b'
                |       'f'
                |       '"'
                |       '\''
                |       '\\'
                |       ('u')+ HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT
                |       '0'..'3'
                        (
                                options {
                                        warnWhenFollowAmbig = false;
                                }
                        :       '0'..'7'
                                (
                                        options {
                                                warnWhenFollowAmbig = false;
                                        }
                                :       '0'..'7'
                                )?
                        )?
                |       '4'..'7'
                        (
                                options {
                                        warnWhenFollowAmbig = false;
                                }
                        :       '0'..'7'
                        )?
                )
        ;


// hexadecimal digit (again, note it's protected)
protected
HEX_DIGIT
        :       ('0'..'9'|
        //'A'..'F'|
        'a'..'f')
        ;


WS    : ( ' '
        | '\r' '\n' {$newline;}
        | '\r' {$newline;}
        | '\n' {$newline;}
        | '\t' {self.tab();}
        )
        {$setType(Token.SKIP);}
      ;    
    

// multiple-line comments
//ML_COMMENT
//      :       "/*"
//              (       /*      '\r' '\n' can be matched in one alternative or by matching
//                              '\r' in one iteration and '\n' in another.  I am trying to
//                              handle any flavor of newline that comes in, but the language
//                              that allows both "\r\n" and "\r" and "\n" to all be valid
//                              newline is ambiguous.  Consequently, the resulting grammar
//                              must be ambiguous.  I'm shutting this warning off.
//                       */
//                      options {
//                              generateAmbigWarnings=false;
//                      }
//              :
//                      { LA(2)!='/' }? '*'
//                      //{ LA(2)!='*' || LA(3) != '}' }? '*'
//              |       '\r' '\n'               {newline();}
//              |       '\r'                    {newline();}
//              |       '\n'                    {newline();}
//              |       ~('*'|'\n'|'\r')
//              )*
//              "*/"
//              {$setType(Token.SKIP);}
//      ;
     

// Annex text processing: derived from multiple-line comments
ANNEX_TEXT
        :       "{**"
                (       /*      '\r' '\n' can be matched in one alternative or by matching
                                '\r' in one iteration and '\n' in another.  I am trying to
                                handle any flavor of newline that comes in, but the language
                                that allows both "\r\n" and "\r" and "\n" to all be valid
                                newline is ambiguous.  Consequently, the resulting grammar
                                must be ambiguous.  I'm shutting this warning off.
                         */
                        options {
                                generateAmbigWarnings=false;
                        }
                :
                        { LA(2)!='*' or LA(3) != '}' }? '*'
                |       '\r' '\n'               {newline();}
                |       '\r'                    {newline();}
                |       '\n'                    {newline();}
                |       ~('*'|'\n'|'\r')
                )*
                "**}"
        ;
 
     
// Single-line comments
SL_COMMENT
        :       "--" (~('\n'|'\r' ))* 
        { $setType(Token.SKIP); }
        ;

# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the appropriate version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to share
# the source code they develop with others or otherwise comply with the
# terms of the GNU General Public License version 2.1.
#
# GNU GPL v. 2.1:
#       This version of DMT is the one to use for the development of
# non-commercial applications, when you are willing to comply
# with the terms of the GNU General Public License version 2.1.
#
# The features of the two licenses are summarized below:
#
#                       Commercial
#                       Developer               GPL
#                       License
#
# License cost          License fee charged     No license fee
#
# Must provide source
# code changes to DMT   No, modifications can   Yes, all source code
#                       be closed               must be provided back
#
# Can create            Yes, that is,           No, applications are subject
# proprietary           no source code needs    to the GPL and all source code
# applications          to be disclosed         must be made available
#
# Support               Yes, 12 months of       No, but available separately
#                       premium technical       for purchase
#                       support
#
# Charge for Runtimes   None                    None
#
vhd = '''library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library leon2ft;
use leon2ft.amba.all;

entity TASTE is
    port (
      clk_i    : in  std_logic;         -- System clock
      reset_n  : in  std_logic;         -- System RST
      -- APB interface
      apbi     : in  apb_slv_in_type;
      apbo     : out apb_slv_out_type
    );
end TASTE;

architecture arch of TASTE is

    -- Circuits for the existing PIs
%(circuits)s
    -- Declare signals
    -- signal CLK : std_logic;
    -- signal RST : std_logic;

    -- Register interface
    -- signal Addr : std_logic_vector(15 downto 0);
    -- signal DataIn : std_logic_vector(7 downto 0);
    -- signal DataOut : std_logic_vector(7 downto 0);
    -- signal WE : std_logic;
    -- signal RE : std_logic;

    -- Registers for I/O
%(ioregisters)s

    -- Signals for start/finish
%(startStopSignals)s

begin

    -- Implement register write
    process (reset_n, clk_i)
    begin
        if (reset_n='1') then
            -- Signals for reset
%(reset)s
        elsif (clk_i'event and clk_i='1') then

            -- Update start-stop pulses
%(updateStartStopPulses)s
            if (apbi.pwrite='1' and apbi.psel= '1' and apbi.penable = '1') then
                case (apbi.paddr(7 downto 0)) is
                      -- Read data
%(readinputdata)s
                 end case;
            end if;
        end if;
    end process;

    -- Implement register read
    process (apbi.paddr, apbi.pwrite, %(outputs)s %(completions)s)
    begin
        if (apbi.pwrite='0' and apbi.psel= '1') then
            case (apbi.paddr(7 downto 0)) is
                -- Write data
%(writeoutputdata)s
                when others => apbo.prdata <= (others => '0');
            end case;
        else
            -- avoid latches
            apbo.prdata <= (others => '0');
        end if;
    end process;

    -- Connections to the VHDL circuits
%(connectionsToSystemC)s

end arch;'''

makefile = r'''
SRCS=Example1.vhd %(pi)s
TARGET=TASTE.bit

all:    ${TARGET}

${TARGET}:      ${SRCS}
%(tab)sxst -intstyle ise -ifn TASTE.xst -ofn TASTE.syr || exit 1
%(tab)sngdbuild -intstyle ise -dd _ngo -aul -nt timestamp -uc ZestSC1.ucf -p xc3s1000-ft256-5 TASTE.ngc TASTE.ngd || exit 1
%(tab)smap -intstyle ise -p xc3s1000-ft256-5 -cm area -ir off -pr b -c 100 -o TASTE_map.ncd TASTE.ngd TASTE.pcf || exit 1
%(tab)spar -w -intstyle ise -ol high -t 1 TASTE_map.ncd TASTE.ncd TASTE.pcf || exit 1
%(tab)strce -intstyle ise -e 3 -s 5 -n 3 -xml TASTE.twx TASTE.ncd -o TASTE.twr TASTE.pcf -ucf ZestSC1.ucf || exit 1
%(tab)sbitgen -intstyle ise -f TASTE.ut TASTE.ncd || exit 1
%(tab)s@echo "========================================"
%(tab)s@echo "      ${TARGET} built successfully.      "
%(tab)s@echo "========================================"

clean:
%(tab)srm -f ${TARGET}
'''

prj = '''vhdl work "craft_gatelibrary.vhd"
vhdl work "ZestSC1_SRAM.vhd"
vhdl work "ZestSC1_Host.vhd"
vhdl work "ZestSC1_Interfaces.vhd"
%(circuits)s
vhdl work "TASTE.vhd"
'''

per_circuit_vhd = """
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

--  Uncomment the following lines to use the declarations that are
--  provided for instantiating Xilinx primitive components.
--library UNISIM;
--use UNISIM.VComponents.all;

%(declaration)s

architecture arch of %(pi)s is

    -- Declare signals
    signal CLK : std_logic;
    signal RST : std_logic;

    type state_type is (
        wait_for_start_signal,
        signal_received,
        work_done
    );
    signal state : state_type := wait_for_start_signal;
begin

    CLK <= clock_%(pi)s;
    RST <= reset_%(pi)s;

    -- Possible clock divider
    process(CLK, RST)
    begin
        if (RST='1') then
            finish_%(pi)s <= '1';
        elsif (CLK'event and CLK='1') then
            case state is
                when wait_for_start_signal =>
                    if start_%(pi)s = '1' then
                        state <= signal_received;
                        finish_%(pi)s <= '0';
                    else
                        state <= wait_for_start_signal;
                    end if;
                when signal_received =>

                    -----------------------------
                    -- Do your processing here --
                    -----------------------------

                    state <= work_done;
                when work_done =>
                    finish_%(pi)s <= '1';
                    state <= wait_for_start_signal;
            end case;
        end if;
    end process;

end arch;
"""

xise = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<project xmlns="http://www.xilinx.com/XMLSchema" xmlns:xil_pn="http://www.xilinx.com/XMLSchema">

  <header>
    <!-- ISE source project file created by Project Navigator.             -->
    <!--                                                                   -->
    <!-- This file contains project source information including a list of -->
    <!-- project source files, project and process properties.  This file, -->
    <!-- along with the project source files, is sufficient to open and    -->
    <!-- implement in ISE Project Navigator.                               -->
    <!--                                                                   -->
    <!-- Copyright (c) 1995-2013 Xilinx, Inc.  All rights reserved. -->
  </header>

  <version xil_pn:ise_version="14.7" xil_pn:schema_version="2"/>

  <files>
    <file xil_pn:name="Example1.vhd" xil_pn:type="FILE_VHDL">
      <association xil_pn:name="BehavioralSimulation" xil_pn:seqID="1"/>
      <association xil_pn:name="Implementation" xil_pn:seqID="5"/>
    </file>
    <file xil_pn:name="ZestSC1_Host.vhd" xil_pn:type="FILE_VHDL">
      <association xil_pn:name="BehavioralSimulation" xil_pn:seqID="2"/>
      <association xil_pn:name="Implementation" xil_pn:seqID="2"/>
    </file>
    <file xil_pn:name="ZestSC1_SRAM.vhd" xil_pn:type="FILE_VHDL">
      <association xil_pn:name="BehavioralSimulation" xil_pn:seqID="3"/>
      <association xil_pn:name="Implementation" xil_pn:seqID="1"/>
    </file>
    <file xil_pn:name="ZestSC1_Interfaces.vhd" xil_pn:type="FILE_VHDL">
      <association xil_pn:name="BehavioralSimulation" xil_pn:seqID="4"/>
      <association xil_pn:name="Implementation" xil_pn:seqID="3"/>
    </file>
    <file xil_pn:name="ZestSC1.ucf" xil_pn:type="FILE_UCF">
      <association xil_pn:name="Implementation" xil_pn:seqID="0"/>
    </file>
    <file xil_pn:name="%(pi)s.vhd" xil_pn:type="FILE_VHDL">
      <association xil_pn:name="BehavioralSimulation" xil_pn:seqID="97"/>
      <association xil_pn:name="Implementation" xil_pn:seqID="4"/>
    </file>
  </files>

  <properties>
    <property xil_pn:name="Allow Unmatched LOC Constraints" xil_pn:value="true" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Device" xil_pn:value="xc3s1000" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Device Family" xil_pn:value="Spartan3" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Drive Done Pin High" xil_pn:value="true" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Enable Enhanced Design Summary" xil_pn:value="false" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Implementation Top" xil_pn:value="Architecture|TASTE|arch" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Implementation Top File" xil_pn:value="Example1.vhd" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Implementation Top Instance Path" xil_pn:value="/TASTE" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Overwrite Compiled Libraries" xil_pn:value="true" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Pack I/O Registers/Latches into IOBs" xil_pn:value="For Inputs and Outputs" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Package" xil_pn:value="ft256" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Preferred Language" xil_pn:value="Verilog" xil_pn:valueState="default"/>
    <property xil_pn:name="Property Specification in Project File" xil_pn:value="Store non-default values only" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Report Fastest Path(s) in Each Constraint" xil_pn:value="false" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Report Fastest Path(s) in Each Constraint Post Trace" xil_pn:value="false" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Report Type" xil_pn:value="Error Report" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Report Type Post Trace" xil_pn:value="Error Report" xil_pn:valueState="non-default"/>
    <property xil_pn:name="Simulator" xil_pn:value="ISim (VHDL/Verilog)" xil_pn:valueState="default"/>
    <property xil_pn:name="Speed Grade" xil_pn:value="-5" xil_pn:valueState="default"/>
    <property xil_pn:name="Synthesis Tool" xil_pn:value="XST (VHDL/Verilog)" xil_pn:valueState="default"/>
    <property xil_pn:name="Top-Level Source Type" xil_pn:value="HDL" xil_pn:valueState="default"/>
    <property xil_pn:name="iMPACT Project File" xil_pn:value="" xil_pn:valueState="non-default"/>
    <!--                                                                                  -->
    <!-- The following properties are for internal use only. These should not be modified.-->
    <!--                                                                                  -->
    <property xil_pn:name="PROP_DesignName" xil_pn:value="Example1" xil_pn:valueState="non-default"/>
    <property xil_pn:name="PROP_DevFamilyPMName" xil_pn:value="spartan3" xil_pn:valueState="default"/>
    <property xil_pn:name="PROP_intProjectCreationTimestamp" xil_pn:value="2016-09-25T12:57:19" xil_pn:valueState="non-default"/>
    <property xil_pn:name="PROP_intWbtProjectID" xil_pn:value="3745F6A05FDE9EEAF3D6AE162B4C5A8F" xil_pn:valueState="non-default"/>
    <property xil_pn:name="PROP_intWorkingDirLocWRTProjDir" xil_pn:value="Same" xil_pn:valueState="non-default"/>
    <property xil_pn:name="PROP_intWorkingDirUsed" xil_pn:value="No" xil_pn:valueState="non-default"/>
    <property xil_pn:name="PROP_mapSmartGuideFileName" xil_pn:value="" xil_pn:valueState="non-default"/>
    <property xil_pn:name="PROP_parSmartGuideFileName" xil_pn:value="" xil_pn:valueState="non-default"/>
  </properties>

  <bindings/>

  <libraries/>

  <autoManagedFiles>
    <!-- The following files are identified by `include statements in verilog -->
    <!-- source files and are automatically managed by Project Navigator.     -->
    <!--                                                                      -->
    <!-- Do not hand-edit this section, as it will be overwritten when the    -->
    <!-- project is analyzed based on files automatically identified as       -->
    <!-- include files.                                                       -->
  </autoManagedFiles>

</project>
"""
